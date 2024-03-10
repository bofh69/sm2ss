#!/usr/bin/env python3

"""
Program to load filaments from Spoolman and create slicer filament configuration.
"""

import argparse
import asyncio
import json
import os
import time
import sys

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import requests

from websockets.client import connect

DEFAULT_TEMPLATE = "default.template"

ORCASLICER = "orcaslicer"
PRUSASLICER = "prusaslicer"
SLICER = "slic3r"
SUPERSLICER = "superslicer"
VERSION = "0.0.1"

parser = argparse.ArgumentParser(
    description="Fetches filaments from Spoolman and creates slicer filament config files.",
)

parser.add_argument(
    "--version", action="version", version="%(prog)s " + VERSION
)
parser.add_argument(
    "-d",
    "--dir",
    metavar="DIR",
    required=True,
    help="the filament config dir",
)

parser.add_argument(
    "-s",
    "--slicer",
    default=SUPERSLICER,
    choices=[ORCASLICER, PRUSASLICER, SLICER, SUPERSLICER],
    help="the slicer",
)

parser.add_argument(
    "-u",
    "--url",
    metavar="URL",
    default="http://mainsailos.local:7912",
    help="URL for the Spoolman installation",
)

parser.add_argument(
    "-U",
    "--updates",
    action="store_true",
    help="keep running and update filament configs if they're updated in Spoolman",
)

parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="verbose output",
)

parser.add_argument(
    "-D",
    "--delete-all",
    action="store_true",
    help="delete all filament configs before adding existing ones",
)

args = parser.parse_args()

loader = FileSystemLoader("templates-" + args.slicer)
templates = Environment(loader=loader)

filament_id_to_filename = {}

filament_usage = {}


def get_config_suffix():
    """Returns the slicer's config file prefix"""
    if args.slicer == SUPERSLICER:
        return "ini"
    if args.slicer == ORCASLICER:
        return "json"

    raise ValueError("That slicer is not yet supported")


def load_filaments(url: str):
    """Load filaments json data from Spoolman"""
    data = requests.get(url, timeout=10)
    return json.loads(data.text)


def get_filament_filename(filament):
    """Returns the filament's config filename"""
    return f"{args.dir}/{filament['vendor']['name']}-{filament['name']}.{get_config_suffix()}"


def delete_filament(filament):
    """Delete the filament's file"""
    old_filename = filament_id_to_filename[filament["id"]]

    print(f"Deleting: {old_filename}")
    os.remove(old_filename)


def delete_all_filaments():
    """Delete all config files in the filament dir"""
    for filename in os.listdir(args.dir):
        if filename.endswith("." + get_config_suffix()):
            filename = args.dir + "/" + filename
            print(f"Deleting: {filename}")
            os.remove(filename)


def write_filament(filament):
    """Output the filament to the right file"""
    filename = get_filament_filename(filament)

    filament_id_to_filename[filament["id"]] = filename

    if "material" in filament:
        template_name = f"{filament['material']}.template"
    else:
        template_name = DEFAULT_TEMPLATE

    try:
        template = templates.get_template(template_name)
        if args.verbose:
            print(f"Using {template_name} as template")
    except TemplateNotFound:
        template = templates.get_template(DEFAULT_TEMPLATE)
        if args.verbose:
            print(f"Using the default template")

    sm2s = {
        "name": parser.prog,
        "version": VERSION,
        "now": time.asctime(),
    }
    filament["sm2s"] = sm2s
    print(f"Writing to: {filename}")

    if args.verbose:
        print("Fields for the template:")
        print(filament)
    filament_text = template.render(filament)

    with open(filename, "w", encoding="utf-8") as cfg_file:
        print(filament_text, file=cfg_file)
    if args.verbose:
        print()


def load_and_update_all_filaments(url: str):
    """Load the filaments from Spoolman and store them in the files"""
    spools = load_filaments(url + "/api/v1/spool")

    for spool in spools:
        write_filament(spool["filament"])


def handle_spool_update_msg(msg):
    """Handles spool update msgs received via WS"""

    spool = msg["payload"]
    filament = spool["filament"]
    filament_id = filament["id"]
    if msg["type"] == "added":
        if filament_id in filament_usage:
            filament_usage[filament_id] += 1
        else:
            filament_usage[filament_id] = 1
        write_filament(filament)
    elif msg["type"] == "updated":
        delete_filament(filament)
        write_filament(filament)
    elif msg["type"] == "deleted":
        filament_id = filament["id"]
        if filament_id in filament_usage:
            filament_usage[filament_id] -= 1
            if filament_usage[filament_id] <= 0:
                # No more usage, remove it
                delete_filament(filament)
    else:
        print(f"Got unknown filament update msg: {msg}")


def handle_filament_update_msg(msg):
    """Handles filamentspool update msgs received via WS"""

    filament = msg["payload"]
    filament_id = filament["id"]
    if msg["type"] == "added":
        pass
    elif msg["type"] == "updated":
        if filament_id in filament_usage:
            # Only update if it was in use
            delete_filament(filament)
            write_filament(filament)
    elif msg["type"] == "deleted":
        pass
    else:
        print(f"Got unknown filament update msg: {msg}")


async def connect_filament_updates():
    """Connect to Spoolman and receive updates to the filaments"""
    async for connection in connect("ws" + args.url[4::] + "/api/v1/filament"):
        async for msg in connection:
            msg = json.loads(msg)
            handle_filament_update_msg(msg)


async def connect_spool_updates():
    """Connect to Spoolman and receive updates to the filaments"""
    async for connection in connect("ws" + args.url[4::] + "/api/v1/spool"):
        async for msg in connection:
            msg = json.loads(msg)
            handle_spool_update_msg(msg)


async def connect_updates():
    """Connect to spoolman to get updates"""
    await asyncio.gather(connect_filament_updates(), connect_spool_updates())


if args.delete_all:
    delete_all_filaments()

try:
    load_and_update_all_filaments(args.url)
except requests.exceptions.ConnectionError as ex:
    print("Could not connect to SpoolMan:")
    print(ex)
    sys.exit(1)

if args.updates:
    print("Waiting for updates...")
    asyncio.run(connect_updates())

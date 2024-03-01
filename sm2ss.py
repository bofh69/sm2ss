#!/usr/bin/env python3

"""
Program to load filaments from Spoolman
and create SuperSlicer filament configuration.
"""

# TODO: Delete old filaments' config during startups
# TODO: Store filaments ids and filename to use during updates

import argparse
import asyncio
import json
import os
import sys

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import requests

from websockets.client import connect

DEFAULT_TEMPLATE = "default.template"

loader = FileSystemLoader("templates")
env = Environment(loader=loader)

parser = argparse.ArgumentParser(
    prog="sm2ss",
    description="Fetches filaments from Spoolman and creates SuperSlicer filament configs.",
)

parser.add_argument(
    "-u",
    "--url",
    metavar="URL",
    default="http://mainsailos.local:7912",
    help="URL for the Spoolman installation",
)
parser.add_argument(
    "-d",
    "--dir",
    metavar="DIR",
    required=True,
    help="SuperSlicer's filament config dir",
)

parser.add_argument(
    "-U",
    "--updates",
    action="store_true",
    help="Keep running and update filament configs if they're updated in Spoolman",
)

args = parser.parse_args()


def load_filaments(url: str):
    """Load filaments json data from Spoolman"""
    data = requests.get(url, timeout=10)
    return json.loads(data.text)


def get_filament_filename(filament):
    """Returns the filament's config filename"""
    return f"{args.dir}/{filament['vendor']['name']}-{filament['name']}.ini"


def delete_filament(filament):
    """Delete the filament's file"""
    filename = get_filament_filename(filament)

    print(f"Deleting: {args.dir}/{filename}")
    os.remove(filename)


def write_filament(filament):
    """Output the filament to the right file"""
    filename = get_filament_filename(filament)

    if "material" in filament:
        template_name = f"{filament['material']}.template"
    else:
        template_name = DEFAULT_TEMPLATE

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        template = env.get_template(DEFAULT_TEMPLATE)

    filament_text = template.render(filament)

    print(f"Writing to: {filename}")
    with open(filename, "w", encoding="utf-8") as cfg_file:
        print(filament_text, file=cfg_file)


def load_and_update_all_filaments(url: str):
    """Load the filaments from Spoolman and store them in the files"""
    filaments = load_filaments(url + "/api/v1/filament")

    for filament in filaments:
        write_filament(filament)


def handle_filament_update_msg(msg):
    """Handles filament update msgs received via WS"""
    if msg["type"] == "added" or msg["type"] == "updated":
        write_filament(msg["payload"])
    elif msg["type"] == "deleted":
        delete_filament(msg["payload"])
    else:
        print(f"Got unknown filament update msg: {msg}")


async def connect_filament_updates():
    """Connect to Spoolman and receive updates to the filaments"""
    async for connection in connect("ws" + args.url[4::] + "/api/v1/filament"):
        async for msg in connection:
            msg = json.loads(msg)
            handle_filament_update_msg(msg)


try:
    load_and_update_all_filaments(args.url)
except requests.exceptions.ConnectionError as ex:
    print("Could not connect to SpoolMan:")
    print(ex)
    sys.exit(1)

if args.updates:
    print("Waiting for updates...")
    asyncio.run(connect_filament_updates())

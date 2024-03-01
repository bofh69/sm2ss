#!/usr/bin/env python3

"""
Program to load filaments from Spoolman
and create SuperSlicer filament configuration.
"""

import argparse
import json
import sys

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import requests

# from websockets.client import connect


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

args = parser.parse_args()


def load_filaments(url: str):
    """Load filaments json data from Spoolman"""
    data = requests.get(url, timeout=10)
    return json.loads(data.text)


def write_filament(filament):
    """Output the filament to the right file"""
    filename = f"{filament['vendor']['name']}-{filament['name']}.ini"
    template_name = f"{filament['material']}.template"

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        template = env.get_template("default.template")

    filament_text = template.render(filament)

    print(f"Writing to: {args.dir}/{filename}")
    with open(f"{args.dir}/{filename}", "w", encoding="utf-8") as cfg_file:
        print(filament_text, file=cfg_file)


def load_and_update_all_filaments(url: str):
    """Load the filaments from Spoolman and store them in the files"""
    filaments = load_filaments(url + "/api/v1/filament")

    # TODO: Clear config-dir's '*.ini' files

    for filament in filaments:
        write_filament(filament)


try:
    load_and_update_all_filaments(args.url)
except requests.exceptions.ConnectionError as ex:
    print("Could not connect to SpoolMan:")
    print(ex)
    sys.exit(1)

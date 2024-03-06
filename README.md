# Spoolman to slicer filament transfer
Create [SuperSlicer](https://github.com/supermerill/SuperSlicer) filament configuration from the filaments in [Spoolman](https://github.com/Donkie/Spoolman).

## Usage

```sh
usage: spoolman2slicer.py [-h] [--version] -d DIR
                          [-s {orcaslicer,prusaslicer,sl1cer,superslicer}]
                          [-u URL] [-U] [-D]

Fetches filaments from Spoolman and creates slicer filament config files.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -d DIR, --dir DIR     the filament config dir
  -s {orcaslicer,prusaslicer,sl1cer,superslicer}, --slicer {orcaslicer,prusaslicer,sl1cer,superslicer}
                        the slicer
  -u URL, --url URL     URL for the Spoolman installation
  -U, --updates         keep running and update filament configs if they're
                        updated in Spoolman
  -D, --delete-all      delete all filament configs before adding existing
                        ones
```

## Prepare for running

Run:
```sh
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Config file templates
spoolman2slicer uses [Jinja2](https://palletsprojects.com/p/jinja/) templates for the configuration files
it creates. They are stored with the filaments' material's name in
`templates/`. If the material's template isn't found,
`default.template` is used.

## Run

```sh
./spoolman2slicer.py -U -d ~/.config/SuperSlicer/filament/
```

See the other options above.

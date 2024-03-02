# Spoolman to Superslicer filament transfer

Spoolman to SuperSlicer filament transfer

## Prepare for running

Run:
```sh
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Config file templates
spoolman2superslicer uses Jinja2 templates for the configuration files
it creates. They are stored with the filaments' material's name in
`templates/`. If the material's template isn't found,
`default.template` is used.

## Run

```sh
./spoolman2superslicer.py -d ~/.config/SuperSlicer/filament/
```

If `-D` is given, all ini files are removed in the directory before
the new ones are created.

'-U' will cause the program to keep running, adding, updating and
deleting files when the filaments are changed in Spoolman.

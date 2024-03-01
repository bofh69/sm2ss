# sm2ss

Spoolman to SuperSlicer filament transfer

## Prepare for running

Run:
```sh
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Config file templates
sm2ss uses Jinja2 templates for the configuration files it creates.
They are stored with the filaments' material's name in `templates/`.
If the material's template isn't found, `default.template` is used.

## Run

```sh
./sm2ss.py -d ~/.config/SuperSlicer/filament/
```

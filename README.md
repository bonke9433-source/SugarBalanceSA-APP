# SugarBalance SA

SugarBalance SA is an offline-first personal health log and food reference app
built with Python, Flet, and SQLite.

## Features

- Record, view, and delete personal blood glucose measurements.
- Browse and search an offline cookbook and culinary herb reference.
- Store measurement data in a local SQLite database; no account or network
  connection is required.
- Switch the interface language between English, isiZulu, isiXhosa, and
  Afrikaans.

This app is for personal record-keeping and general food information. It does
not diagnose, interpret measurements, or replace advice from a qualified
healthcare professional. Herbs and spices are not presented as treatments.
Talk to a healthcare professional before changing medication or using
supplements.

## Run

Use Python 3.10 or newer:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

The SQLite database is saved locally at `data/sugarbalance.db`.

## Tests

```powershell
python -m unittest discover -s tests
```

## Architecture

- `main.py`: Flet presentation layer (Tracker, Cookbook, and Herbs screens).
- `database.py`: SQLite health-log persistence and validation.
- `recipes.py`: offline recipe data and search.
- `herbs.py`: offline herb data and search.
- `localization/`: JSON interface translations.
- `data/`: local SQLite database storage.

SQLite on the user's device is the source of truth. The MVP reads and writes
health logs locally and does not require a server or internet connection.
Health-log changes are recorded in a local sync queue, but no sync worker or
backend is implemented yet. A future sync worker should send queued changes
from local SQLite without making the server the source of truth. An optional
WhatsApp reminder or notification could follow a successful sync, but should
require explicit user opt-in and must not send sensitive glucose or
blood-pressure values in messages.

The current language catalogs translate interface labels and app messages.
Recipe and herbal reference content remains in English until reviewed
translations are available. In particular, medical and safety translations
should be checked by fluent speakers and qualified health professionals before
being relied on.
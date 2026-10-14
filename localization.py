"""Load and validate the app's offline language catalogs."""

import json
from pathlib import Path
from string import Formatter

LOCALIZATION_DIR = Path(__file__).resolve().parent / "localization"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zu": "isiZulu",
    "xh": "isiXhosa",
    "af": "Afrikaans",
}


def load_translations(language: str) -> dict[str, str]:
    """Load a complete catalog and report missing or invalid translations."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    catalogs: dict[str, dict[str, str]] = {}
    for code in ("en", language):
        path = LOCALIZATION_DIR / f"{code}.json"
        with path.open(encoding="utf-8") as catalog_file:
            catalog = json.load(catalog_file)
        if not isinstance(catalog, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in catalog.items()
        ):
            raise ValueError(f"Language catalog must contain string values: {path}")
        catalogs[code] = catalog

    english_keys = set(catalogs["en"])
    selected_keys = set(catalogs[language])
    missing = english_keys - selected_keys
    extra = selected_keys - english_keys
    if missing or extra:
        raise ValueError(
            f"Invalid {language} catalog keys; missing: {sorted(missing)}, "
            f"extra: {sorted(extra)}"
        )
    for key, english_text in catalogs["en"].items():
        english_fields = {
            field
            for _, field, _, _ in Formatter().parse(english_text)
            if field is not None
        }
        translated_fields = {
            field
            for _, field, _, _ in Formatter().parse(catalogs[language][key])
            if field is not None
        }
        if english_fields != translated_fields:
            raise ValueError(
                f"Invalid format placeholders in {language} translation for {key}."
            )
    return catalogs[language]

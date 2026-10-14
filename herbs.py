"""Offline herbal information with general medication-safety guidance."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Herb:
    id: str
    name: str
    local_names: tuple[str, ...]
    traditional_use: str
    evidence_note: str
    medication_warning: str
    red_flags: tuple[str, ...]


HERBAL_INFORMATION = (
    Herb(
        id="H001",
        name="Bitter Gourd / Bitter Melon",
        local_names=("Bitter gourd", "Bitter melon"),
        traditional_use=(
            "Traditionally consumed or used in some communities in connection "
            "with blood-sugar management."
        ),
        evidence_note=(
            "Research into blood-glucose effects is ongoing and evidence is not "
            "strong enough to treat this as a replacement for prescribed "
            "diabetes treatment."
        ),
        medication_warning=(
            "May potentially affect blood glucose. Combining it with "
            "glucose-lowering medication could potentially contribute to "
            "excessively low glucose."
        ),
        red_flags=(
            "Do not replace prescribed diabetes medication.",
            "Speak with a healthcare professional before using it regularly "
            "alongside diabetes medication.",
            "Seek medical advice if experiencing symptoms of low blood glucose.",
        ),
    ),
    Herb(
        id="H002",
        name="Cinnamon",
        local_names=("Cinnamon",),
        traditional_use=(
            "Commonly used as a culinary spice and sometimes used traditionally "
            "in preparations associated with blood-sugar management."
        ),
        evidence_note="Evidence regarding meaningful glucose-lowering benefits is mixed.",
        medication_warning=(
            "Do not assume cinnamon can replace prescribed diabetes treatment. "
            "Some forms and large amounts may present additional safety concerns."
        ),
        red_flags=(
            "Food use is different from concentrated supplements.",
            "Discuss regular medicinal use with a healthcare professional.",
            "Do not stop prescribed medication.",
        ),
    ),
    Herb(
        id="H003",
        name="Aloe Ferox",
        local_names=("Aloe ferox",),
        traditional_use=(
            "A South African plant with a long history of traditional and "
            "medicinal use."
        ),
        evidence_note=(
            "Different preparations can have very different effects. "
            "Traditional use should not be interpreted as proof of safety or "
            "effectiveness for diabetes or hypertension."
        ),
        medication_warning=(
            "Certain aloe preparations can have laxative effects and may affect "
            "fluid and electrolyte balance. This may be important for people "
            "taking medicines or managing chronic conditions."
        ),
        red_flags=(
            "Do not self-treat diabetes or hypertension with aloe.",
            "Avoid medicinal preparations without professional guidance.",
            "Discuss use with a pharmacist, doctor or clinic.",
        ),
    ),
)

GENERAL_HERBAL_WARNING = (
    "IMPORTANT SAFETY NOTICE\n\n"
    "Traditional remedies and supplements can interact with prescription medicines.\n\n"
    "Never stop, reduce or replace prescribed medication because of information "
    "in this application.\n\n"
    "If you take medicines such as metformin, insulin, warfarin, blood-pressure "
    "medication or other chronic medicines, speak to a doctor or pharmacist "
    "before regularly using medicinal herbs or supplements.\n\n"
    "Seek urgent medical care for severe symptoms."
)


def get_all_herbs() -> list[Herb]:
    """Return all offline herb entries."""
    return list(HERBAL_INFORMATION)


def get_herb(herb_id: str) -> Optional[Herb]:
    """Return an herb by ID, or None if it is not in the reference."""
    return next((herb for herb in HERBAL_INFORMATION if herb.id == herb_id), None)


def search_herbs(query: str = "") -> list[Herb]:
    """Search every herb field; all query words must match."""
    terms = query.casefold().split()
    if not terms:
        return get_all_herbs()

    matches = []
    for herb in HERBAL_INFORMATION:
        searchable_text = " ".join(
            (
                herb.id,
                herb.name,
                *herb.local_names,
                herb.traditional_use,
                herb.evidence_note,
                herb.medication_warning,
                *herb.red_flags,
            )
        ).casefold()
        if all(term in searchable_text for term in terms):
            matches.append(herb)
    return matches

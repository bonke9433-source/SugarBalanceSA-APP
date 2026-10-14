import unittest

from herbs import (
    GENERAL_HERBAL_WARNING,
    get_all_herbs,
    get_herb,
    search_herbs,
)


class HerbReferenceTests(unittest.TestCase):
    def test_get_all_herbs_returns_all_entries(self) -> None:
        herbs = get_all_herbs()

        self.assertEqual([herb.id for herb in herbs], ["H001", "H002", "H003"])

    def test_get_herb_returns_entry_or_none(self) -> None:
        self.assertEqual(get_herb("H003").name, "Aloe Ferox")
        self.assertIsNone(get_herb("missing"))

    def test_search_matches_names_local_names_and_safety_details(self) -> None:
        self.assertEqual(
            [herb.id for herb in search_herbs("BITTER MELON")],
            ["H001"],
        )
        self.assertEqual(
            [herb.id for herb in search_herbs("electrolyte aloe")],
            ["H003"],
        )

    def test_empty_search_returns_all_entries(self) -> None:
        self.assertEqual(search_herbs("  "), get_all_herbs())

    def test_general_warning_covers_medication_and_urgent_care(self) -> None:
        self.assertIn("Never stop, reduce or replace prescribed medication", GENERAL_HERBAL_WARNING)
        self.assertIn("Seek urgent medical care", GENERAL_HERBAL_WARNING)


if __name__ == "__main__":
    unittest.main()

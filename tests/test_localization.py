import unittest

from localization import SUPPORTED_LANGUAGES, load_translations


class LocalizationTests(unittest.TestCase):
    def test_all_language_catalogs_have_the_same_keys(self) -> None:
        english_keys = set(load_translations("en"))

        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                self.assertEqual(set(load_translations(language)), english_keys)

    def test_catalog_contains_basic_translated_ui_labels(self) -> None:
        self.assertEqual(load_translations("zu")["nav_tracker"], "Impilo")
        self.assertEqual(load_translations("xh")["nav_cookbook"], "Ukupheka")
        self.assertEqual(load_translations("af")["nav_herbs"], "Kruie")

    def test_unsupported_language_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_translations("fr")


if __name__ == "__main__":
    unittest.main()

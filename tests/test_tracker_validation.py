import unittest

from main import (
    _parse_health_readings,
    _parse_optional_glucose,
    _parse_optional_int,
)


class TrackerValidationTests(unittest.TestCase):
    def test_blank_optional_fields_return_none(self) -> None:
        self.assertIsNone(_parse_optional_int(None, "Systolic pressure"))
        self.assertIsNone(_parse_optional_int("  ", "Systolic pressure"))
        self.assertIsNone(_parse_optional_glucose(""))

    def test_integer_field_requires_positive_whole_number(self) -> None:
        self.assertEqual(_parse_optional_int("120", "Systolic pressure"), 120)
        for value in ("abc", "120.5", "0", "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _parse_optional_int(value, "Systolic pressure")

    def test_glucose_field_requires_positive_finite_number(self) -> None:
        self.assertEqual(_parse_optional_glucose("5.6"), 5.6)
        for value in ("abc", "0", "-1", "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _parse_optional_glucose(value)

    def test_health_readings_require_both_blood_pressure_values_or_glucose(self) -> None:
        self.assertEqual(
            _parse_health_readings("120", "80", ""),
            (120, 80, None),
        )
        self.assertEqual(
            _parse_health_readings("", "", "5.6"),
            (None, None, 5.6),
        )
        for systolic, diastolic in (("120", ""), ("", "80"), ("", "",)):
            with self.subTest(systolic=systolic, diastolic=diastolic):
                with self.assertRaises(ValueError):
                    _parse_health_readings(systolic, diastolic, "")


if __name__ == "__main__":
    unittest.main()

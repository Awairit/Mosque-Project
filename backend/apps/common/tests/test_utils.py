from django.test import SimpleTestCase
from apps.common.utils.strings import normalize_phone_number

class PhoneNormalizationTests(SimpleTestCase):
    def test_already_e164(self):
        self.assertEqual(normalize_phone_number("+919876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("+966512345678"), "+966512345678")

    def test_local_numbers_prepending(self):
        # Default prepends +91
        self.assertEqual(normalize_phone_number("9876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number(" 98765 43210 "), "+919876543210")
        self.assertEqual(normalize_phone_number("98765-43210"), "+919876543210")

    def test_local_numbers_with_explicit_country_code(self):
        self.assertEqual(normalize_phone_number("512345678", default_country_code="+966"), "+966512345678")
        self.assertEqual(normalize_phone_number("512345678", default_country_code="966"), "+966512345678")

    def test_local_starting_with_cc(self):
        # If it already starts with the country code digits (e.g. 91)
        self.assertEqual(normalize_phone_number("919876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("966512345678", default_country_code="+966"), "+966512345678")

    def test_invalid_formats_raise_value_error(self):
        with self.assertRaises(ValueError):
            normalize_phone_number("")
        with self.assertRaises(ValueError):
            normalize_phone_number("abc")
        with self.assertRaises(ValueError):
            normalize_phone_number("+12")  # too short
        with self.assertRaises(ValueError):
            normalize_phone_number("123456")  # too short

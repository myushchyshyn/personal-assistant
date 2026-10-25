"""Тести валідації полів контакту та нотатки."""

import unittest
from datetime import date

from personal_assistant.fields import (
    Birthday,
    ContactTag,
    Email,
    FirstName,
    LastName,
    NoteTags,
    Phone,
    format_phone,
)


class PhoneTests(unittest.TestCase):
    def test_accepts_international_format_with_mask(self):
        self.assertEqual(Phone("+380 (50) 123-45-67").value, "380501234567")

    def test_adds_country_code_to_nine_digits(self):
        # Користувач прибрав +380 на початку і ввів лише 9 цифр
        self.assertEqual(Phone("501234567").value, "380501234567")

    def test_replaces_leading_zero_with_country_code(self):
        self.assertEqual(Phone("0501234567").value, "380501234567")

    def test_formats_phone_with_mask(self):
        self.assertEqual(str(Phone("0501234567")), "+380(50)123-45-67")
        self.assertEqual(format_phone("380501234567"), "+380(50)123-45-67")

    def test_rejects_foreign_or_short_numbers(self):
        for raw in ("12345", "+49 1234567890", "", "+380 50"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                Phone(raw)


class EmailTests(unittest.TestCase):
    def test_valid_email(self):
        self.assertEqual(Email("anna@example.com").value, "anna@example.com")

    def test_empty_email_is_none(self):
        self.assertIsNone(Email("").value)
        self.assertIsNone(Email(None).value)
        self.assertIsNone(Email("-").value)

    def test_invalid_email(self):
        with self.assertRaises(ValueError):
            Email("anna@example")


class BirthdayTests(unittest.TestCase):
    def test_parses_date(self):
        self.assertEqual(Birthday("05.03.1990").value, date(1990, 3, 5))

    def test_rejects_wrong_date_and_future(self):
        with self.assertRaises(ValueError):
            Birthday("31.02.1990")
        with self.assertRaises(ValueError):
            Birthday("01.01.2999")

    def test_days_until_birthday(self):
        birthday = Birthday("10.11.1990")
        self.assertEqual(birthday.days_until(date(2026, 10, 25)), 16)

    def test_birthday_today_is_zero_days(self):
        birthday = Birthday("25.10.1990")
        self.assertEqual(birthday.days_until(date(2026, 10, 25)), 0)

    def test_leap_day_moves_to_march_first(self):
        birthday = Birthday("29.02.2000")
        self.assertEqual(
            birthday.next_occurrence(date(2027, 1, 1)), date(2027, 3, 1)
        )


class NameTests(unittest.TestCase):
    def test_accepts_letters_with_dash(self):
        self.assertEqual(FirstName("Анна-Марія").value, "Анна-Марія")

    def test_rejects_digits_and_empty(self):
        for raw in ("Ann3", "", "   "):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                FirstName(raw)


class AutoCorrectionTests(unittest.TestCase):
    def test_name_gets_capital_letters(self):
        self.assertEqual(FirstName("анна").value, "Анна")
        self.assertEqual(FirstName("анна-марія").value, "Анна-Марія")
        self.assertEqual(LastName("о'нил").value, "О'Нил")
        self.assertEqual(LastName("коваль шевченко").value, "Коваль Шевченко")

    def test_name_correction_is_reported(self):
        self.assertEqual(len(FirstName("анна").corrections), 1)
        self.assertEqual(FirstName("Анна").corrections, [])

    def test_phone_without_code_is_reported(self):
        self.assertEqual(
            Phone("501234567").corrections,
            ["номер без коду країни: додано +380 автоматично"],
        )
        self.assertEqual(len(Phone("0501234567").corrections), 1)

    def test_full_phone_is_not_corrected(self):
        self.assertEqual(Phone("+380501234567").corrections, [])


class ContactTagTests(unittest.TestCase):
    def test_tag_is_lowercase_with_hash(self):
        self.assertEqual(ContactTag("#Робота").value, "#робота")
        self.assertEqual(ContactTag("#сім'я").value, "#сім'я")

    def test_tag_without_hash_is_rejected(self):
        for raw in ("робота", "два слова", "#два слова", "#"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                ContactTag(raw)


class NoteTagsTests(unittest.TestCase):
    def test_parses_tags_and_removes_duplicates(self):
        self.assertEqual(
            NoteTags("#Робота #ідеї #робота").value, ["#робота", "#ідеї"]
        )

    def test_tag_without_hash_is_rejected(self):
        with self.assertRaises(ValueError):
            NoteTags("tag1")

    def test_empty_tags_are_none(self):
        self.assertIsNone(NoteTags("").value)
        self.assertIsNone(NoteTags("-").value)


if __name__ == "__main__":
    unittest.main()

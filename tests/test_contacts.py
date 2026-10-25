"""Тести контактів і адресної книги."""

import unittest
from datetime import date

from personal_assistant.contacts import AddressBook, Record


def make_record(first="Анна", last="Коваль", tag="#друзі", phone="0501234567",
                birthday=None, email=None):
    """Створює контакт із типовими значеннями для тестів."""
    return Record(first, last, "Київ, вул. Хрещатик, 1", phone, tag,
                  email=email, birthday=birthday)


class RecordTests(unittest.TestCase):
    def test_fields_are_validated(self):
        with self.assertRaises(ValueError):
            make_record(phone="123")

    def test_update_changes_one_field(self):
        record = make_record()
        record.update("address", "Львів")
        self.assertEqual(record.address.value, "Львів")

    def test_update_unknown_field_is_rejected(self):
        with self.assertRaises(ValueError):
            make_record().update("passport", "AB123")

    def test_matches_by_any_field_and_phone_digits(self):
        record = make_record(email="anna@example.com")
        self.assertTrue(record.matches("коваль"))
        self.assertTrue(record.matches("0501234"))
        self.assertTrue(record.matches("anna@example"))
        self.assertFalse(record.matches("Одеса"))


class AddressBookTests(unittest.TestCase):
    def setUp(self):
        self.book = AddressBook()
        self.book.add_record(make_record("Анна", "Коваль", tag="#друзі"))
        self.book.add_record(make_record("Петро", "Сидоренко", tag="#робота",
                                         phone="0671112233"))

    def test_duplicate_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.book.add_record(make_record("анна", "коваль"))

    def test_find_is_case_insensitive(self):
        self.assertIsNotNone(self.book.find("  АННА коваль "))
        self.assertIsNone(self.book.find("Невідомий Контакт"))

    def test_search_returns_matching_records(self):
        found = self.book.search("сидоренко")
        self.assertEqual([r.full_name for r in found], ["Петро Сидоренко"])

    def test_group_by_tag_is_sorted(self):
        groups = self.book.group_by_tag()
        self.assertEqual(list(groups), ["#друзі", "#робота"])

    def test_rename_needs_rebuild_keys(self):
        record = self.book.find("Анна Коваль")
        record.update("last_name", "Шевченко")
        self.book.rebuild_keys()
        self.assertIsNotNone(self.book.find("Анна Шевченко"))
        self.assertIsNone(self.book.find("Анна Коваль"))

    def test_upcoming_birthdays_exact_days(self):
        self.book.add_record(make_record("Оля", "Тест",
                                         birthday="10.11.1990"))
        today = date(2026, 10, 25)
        found = self.book.upcoming_birthdays(16, today=today)
        self.assertEqual([r.full_name for r in found], ["Оля Тест"])
        self.assertEqual(self.book.upcoming_birthdays(15, today=today), [])


if __name__ == "__main__":
    unittest.main()

"""Тести збереження даних на диск."""

import tempfile
import unittest
from pathlib import Path

from personal_assistant.contacts import AddressBook, Record
from personal_assistant.notes import NoteBook
from personal_assistant.storage import load_data, save_data


class StorageTests(unittest.TestCase):
    def setUp(self):
        # Тимчасова папка, щоб тести не чіпали справжні дані користувача
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "data.pkl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_gives_empty_books(self):
        contacts, notes = load_data(self.path)
        self.assertEqual(len(contacts), 0)
        self.assertEqual(len(notes), 0)

    def test_data_survives_restart(self):
        contacts = AddressBook()
        contacts.add_record(Record("Анна", "Коваль", "Київ", "0501234567",
                                   "друзі", email="anna@example.com"))
        notes = NoteBook()
        notes.add("Заголовок", "Текст", "#тест", "Анна Коваль")
        save_data(contacts, notes, self.path)

        loaded_contacts, loaded_notes = load_data(self.path)
        record = loaded_contacts.find("Анна Коваль")
        self.assertEqual(str(record.phone), "+380(50)123-45-67")
        self.assertEqual(str(record.email), "anna@example.com")
        self.assertEqual(loaded_notes.find(1).contact_name, "Анна Коваль")

    def test_corrupted_file_raises_clear_error(self):
        self.path.write_bytes(b"not a pickle")
        with self.assertRaises(ValueError):
            load_data(self.path)


if __name__ == "__main__":
    unittest.main()

"""Тести нотаток: теги, пошук, групування і прив'язка до контактів."""

import unittest

from personal_assistant.notes import NoteBook


class NoteBookTests(unittest.TestCase):
    def setUp(self):
        self.notes = NoteBook()
        self.first = self.notes.add(
            "План", "Купити молоко", "#побут #термінове", "Анна Коваль"
        )
        self.second = self.notes.add("Ідея", "Нова книга", "#ідеї")

    def test_ids_increase(self):
        self.assertEqual([self.first.note_id, self.second.note_id], [1, 2])

    def test_search_by_text_tag_and_contact(self):
        self.assertEqual(len(self.notes.search("молоко")), 1)
        self.assertEqual(len(self.notes.search("#ідеї")), 1)
        self.assertEqual(len(self.notes.search("коваль")), 1)
        self.assertEqual(self.notes.search("неіснуюче"), [])

    def test_find_by_tag(self):
        found = self.notes.find_by_tag("#побут")
        self.assertEqual([note.note_id for note in found], [1])

    def test_group_by_tags_puts_note_in_each_group(self):
        groups = self.notes.group_by_tags()
        self.assertEqual(list(groups), ["#побут", "#термінове", "#ідеї"])
        self.assertEqual(len(groups["#побут"]), 1)

    def test_rename_contact_moves_link(self):
        self.notes.rename_contact("анна коваль", "Анна Шевченко")
        self.assertEqual(self.first.contact_name, "Анна Шевченко")
        self.assertEqual(len(self.notes.find_by_contact("Анна Шевченко")), 1)

    def test_unlink_contact_clears_link(self):
        self.notes.unlink_contact("Анна Коваль")
        self.assertIsNone(self.first.contact_name)

    def test_update_fields(self):
        self.first.update("tags", "#новий")
        self.assertEqual(self.first.tags, ["#новий"])
        self.first.update("tags", "-")
        self.assertEqual(self.first.tags, [])
        with self.assertRaises(ValueError):
            self.first.update("color", "red")


if __name__ == "__main__":
    unittest.main()

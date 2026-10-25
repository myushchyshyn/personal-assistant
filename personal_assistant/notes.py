"""Нотатки: заголовок, текст, теги з # та прив'язка до контакту."""

from collections import UserDict, defaultdict

from .colors import paint_tag
from .fields import NoteTags, TextField


class Title(TextField):
    """Заголовок нотатки, обов'язковий."""

    label = "Заголовок"


class NoteText(TextField):
    """Текст нотатки, обов'язковий."""

    label = "Текст нотатки"


class Note:
    """Одна нотатка. Може бути прив'язана до контакту за його повним ім'ям."""

    def __init__(self, note_id, title, text, tags=None, contact_name=None):
        self.note_id = note_id
        self.title = Title(title)
        self.text = NoteText(text)
        # NoteTags повертає список тегів або None, якщо тегів немає
        self.tags = NoteTags(tags).value or []
        self.contact_name = contact_name

    def update(self, field, raw_value):
        """Замінює заголовок, текст або теги після перевірки."""
        if field == "title":
            self.title = Title(raw_value)
        elif field == "text":
            self.text = NoteText(raw_value)
        elif field == "tags":
            self.tags = NoteTags(raw_value).value or []
        else:
            raise ValueError("Такого поля нотатки немає.")

    def matches(self, query):
        """Чи є query у заголовку, тексті, тегах або імені контакту."""
        query = query.lower()
        texts = [
            str(self.title),
            str(self.text),
            " ".join(self.tags),
            self.contact_name or "",
        ]
        return any(query in text.lower() for text in texts)

    def __str__(self):
        tags = " ".join(paint_tag(tag) for tag in self.tags) or "-"
        contact = self.contact_name or "-"
        return (
            f"[{self.note_id}] {self.title}\n"
            f"    {self.text}\n"
            f"    Теги: {tags}\n"
            f"    Контакт: {contact}"
        )


class NoteBook(UserDict):
    """Сховище нотаток за числовим номером (id)."""

    def add(self, title, text, tags=None, contact_name=None):
        # Новий номер — на одиницю більший за найбільший наявний
        note_id = max(self.data, default=0) + 1
        note = Note(note_id, title, text, tags, contact_name)
        self.data[note_id] = note
        return note

    def find(self, note_id):
        """Повертає нотатку за номером або None."""
        return self.data.get(note_id)

    def search(self, query):
        """Нотатки, у яких будь-яке поле містить query."""
        return [note for note in self.data.values() if note.matches(query)]

    def find_by_tag(self, tag):
        """Нотатки з тегом (наприклад, '#робота')."""
        return [note for note in self.data.values() if tag in note.tags]

    def group_by_tags(self):
        """Групує нотатки за тегами. Нотатка з кількома тегами в усіх них."""
        groups = defaultdict(list)
        for note in self.data.values():
            for tag in note.tags:
                groups[tag].append(note)
        return {tag: groups[tag] for tag in sorted(groups)}

    def find_by_contact(self, full_name):
        """Нотатки, прив'язані до контакту з цим ім'ям."""
        return [note for note in self.data.values()
                if _same_name(note.contact_name, full_name)]

    def rename_contact(self, old_name, new_name):
        """Переносить прив'язку нотаток після зміни імені контакту."""
        for note in self.find_by_contact(old_name):
            note.contact_name = new_name

    def unlink_contact(self, full_name):
        """Знімає прив'язку нотаток, коли контакт видалено."""
        for note in self.find_by_contact(full_name):
            note.contact_name = None


def _same_name(first, second):
    """Порівнює імена без урахування регістру. None ні з чим не збігається."""
    return first is not None and first.lower() == second.lower()

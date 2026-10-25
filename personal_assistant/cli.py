"""Командний інтерфейс «Персональний помічник».

Програма працює в циклі: користувач вводить команду, програма її виконує
і чекає наступну, доки не буде введено exit. Помилки введення показуються
повідомленням, але програма не закривається.
"""

import copy
import os
import sys

from .contacts import AddressBook, Record
from .fields import (
    PHONE_TEMPLATE,
    Address,
    Birthday,
    ContactTag,
    Email,
    FirstName,
    LastName,
    NoteTags,
    Phone,
)
from .notes import NoteBook, NoteText, Title
from .storage import DATA_FILE, load_data, save_data

# Поля контакту: (назва атрибута, підпис для користувача, клас поля)
CONTACT_FIELDS = [
    ("first_name", "Ім'я", FirstName),
    ("last_name", "Прізвище", LastName),
    ("address", "Адреса", Address),
    ("phone", f"Телефон ({PHONE_TEMPLATE})", Phone),
    ("tag", "Тег контакту (наприклад, сім'я або робота)", ContactTag),
    ("email", "Email", Email),
    ("birthday", "День народження ДД.ММ.РРРР", Birthday),
]

# Скорочення команд: коротка назва -> повна назва команди
ALIASES = {
    # Контакти
    "a": "add-contact",
    "l": "contacts",
    "e": "edit-contact",
    "d": "delete-contact",
    "s": "search-contact",
    "g": "sort-contacts",
    "b": "birthdays",
    # Нотатки: префікс n + літера
    "na": "add-note",
    "nl": "notes",
    "ne": "edit-note",
    "nd": "delete-note",
    "ns": "search-note",
    "nt": "find-tag",
    "ng": "sort-notes",
    "nc": "contact-notes",
    # Загальні
    "h": "help",
    "q": "exit",
}
EXIT_COMMANDS = ("exit",)

# Поля нотатки, які можна редагувати (прив'язку до контакту — окремо)
NOTE_FIELDS = [
    ("title", "Заголовок", Title),
    ("text", "Текст", NoteText),
    ("tags", "Теги з # (наприклад, #робота #ідеї)", NoteTags),
]


def read_line(prompt):
    """Читає рядок з клавіатури. Некоректні байти дають помилку, не падіння."""
    try:
        return input(prompt)
    except UnicodeDecodeError:
        raise ValueError(
            "Термінал надіслав некоректні символи. "
            "Перевірте, що він працює в кодуванні UTF-8."
        ) from None


def ask_field(label, field_class, skip_hint=None):
    """Питає значення, доки воно не пройде перевірку поля field_class.

    Якщо skip_hint задано, порожній ввід повертає None (поле пропущено).
    """
    if skip_hint is None:
        prompt = f"{label}: "
    else:
        prompt = f"{label} (Enter — {skip_hint}): "
    while True:
        raw = read_line(prompt).strip()
        if not raw and skip_hint is not None:
            return None
        try:
            field_class(raw)  # перевірка; сам запис створить Record або Note
            return raw
        except ValueError as error:
            print(f"Помилка: {error} Спробуйте ще раз.")


def pick_by_number(items, raw):
    """Повертає елемент списку за номером, який ввів користувач (з 1)."""
    if not raw.isdigit() or not 1 <= int(raw) <= len(items):
        raise ValueError("Немає пункту з таким номером.")
    return items[int(raw) - 1]


def confirm(question):
    """Просить підтвердити дію. Повертає True, якщо відповідь «так»."""
    answer = read_line(f"{question} (так/ні): ").strip().lower()
    return answer in ("так", "т", "yes", "y")


def print_records(records):
    """Виводить контакти з роздільником між ними."""
    for record in records:
        print(record)
        print("-" * 30)


def print_notes(notes):
    """Виводить нотатки з порожнім рядком між ними."""
    for note in notes:
        print(note)
        print()


class PersonalAssistant:
    """Застосунок: тримає контакти й нотатки та виконує команди користувача."""

    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.contacts, self.notes = load_data(data_file)
        # Команда -> (опис для довідки, метод, який її виконує)
        self.commands = {
            "add-contact": ("Додати контакт", self.add_contact),
            "contacts": ("Показати всі контакти", self.show_contacts),
            "edit-contact": ("Редагувати контакт", self.edit_contact),
            "delete-contact": ("Видалити контакт", self.delete_contact),
            "search-contact": ("Пошук контактів", self.search_contacts),
            "sort-contacts": ("Контакти за тегами", self.sort_contacts),
            "birthdays": ("Дні народження через N днів", self.show_birthdays),
            "add-note": ("Додати нотатку", self.add_note),
            "notes": ("Показати всі нотатки", self.show_notes),
            "edit-note": ("Редагувати нотатку", self.edit_note),
            "delete-note": ("Видалити нотатку", self.delete_note),
            "search-note": ("Пошук нотаток", self.search_notes),
            "find-tag": ("Нотатки з конкретним тегом", self.find_notes_by_tag),
            "sort-notes": ("Нотатки, згруповані за тегами", self.sort_notes),
            "contact-notes": ("Нотатки, прив'язані до контакту",
                              self.show_contact_notes),
            "help": ("Список команд", self.show_help),
        }

    def run(self):
        """Головний цикл: читає команду, виконує її, повторює до exit."""
        print("Ласкаво просимо до «Персональний помічник»!")
        print("Введіть help (h), щоб побачити команди, або exit (q) — вихід.")
        while True:
            try:
                command = read_line("\nКоманда: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nДо побачення!")
                break
            except ValueError as error:
                print(f"Помилка: {error}")
                continue
            # Скорочення замінюємо на повну назву команди
            command = ALIASES.get(command, command)
            if command in EXIT_COMMANDS:
                print("До побачення!")
                break
            if not command:
                continue
            if command not in self.commands:
                print("Невідома команда. Введіть help (h) — список команд.")
                continue
            self.execute(self.commands[command][1])

    def execute(self, action):
        """Виконує дію і перехоплює помилки, щоб програма не закрилась."""
        try:
            changed = action()
        except ValueError as error:
            print(f"Помилка: {error}")
        except KeyboardInterrupt:
            print("\nДію скасовано.")
        else:
            if changed:
                self.save()

    def save(self):
        """Зберігає дані на диск. Помилка запису показується користувачу."""
        try:
            save_data(self.contacts, self.notes, self.data_file)
        except OSError as error:
            print(f"Не вдалося зберегти дані: {error}")

    # ----- Контакти -----

    def ask_contact(self):
        """Питає повне ім'я і повертає знайдений контакт."""
        full_name = read_line("Повне ім'я контакту (Ім'я Прізвище): ").strip()
        record = self.contacts.find(full_name)
        if record is None:
            raise ValueError("Контакт з таким ім'ям не знайдено.")
        return record

    def add_contact(self):
        """Питає всі поля контакту, перевіряє їх і додає запис."""
        values = {}
        for field, label, field_class in CONTACT_FIELDS:
            skip_hint = "пропустити" if field_class.optional else None
            values[field] = ask_field(label, field_class, skip_hint)
        self.contacts.add_record(Record(**values))
        print("Контакт додано.")
        return True

    def show_contacts(self):
        if not self.contacts:
            print("Контактів ще немає.")
            return False
        records = sorted(self.contacts.values(), key=lambda r: r.key)
        print_records(records)
        return False

    def edit_contact(self):
        """Змінює одне поле контакту. Enter без значення — нічого не змінює."""
        record = self.ask_contact()
        print(record)
        for number, (_, label, _) in enumerate(CONTACT_FIELDS, start=1):
            print(f"  {number}. {label}")
        choice = read_line("Номер поля (Enter — скасувати): ").strip()
        if not choice:
            return False
        field, label, field_class = pick_by_number(CONTACT_FIELDS, choice)
        new_value = ask_field(f"Нове значення для «{label}»", field_class,
                              "без змін")
        if new_value is None:
            print("Поле не змінено.")
            return False

        old_name = record.full_name
        backup = copy.copy(record)
        record.update(field, new_value)
        # Якщо після зміни імені такий контакт уже є — повертаємо все назад
        if self.contacts.find(record.full_name) not in (None, record):
            record.__dict__.update(backup.__dict__)
            raise ValueError("Контакт з таким ім'ям і прізвищем уже існує.")
        self.contacts.rebuild_keys()
        if record.full_name != old_name:
            self.notes.rename_contact(old_name, record.full_name)
        print("Контакт оновлено.")
        return True

    def delete_contact(self):
        record = self.ask_contact()
        if not confirm(f"Видалити контакт {record.full_name}?"):
            print("Видалення скасовано.")
            return False
        del self.contacts[record.key]
        self.notes.unlink_contact(record.full_name)
        print("Контакт видалено.")
        return True

    def search_contacts(self):
        query = read_line("Що шукаємо (ім'я, телефон, email, тег…): ").strip()
        if not query:
            raise ValueError("Пошуковий запит не може бути порожнім.")
        found = self.contacts.search(query)
        if found:
            print_records(found)
        else:
            print("Нічого не знайдено.")
        return False

    def sort_contacts(self):
        """Виводить контакти, згруповані за тегом."""
        if not self.contacts:
            print("Контактів ще немає.")
            return False
        for tag, records in self.contacts.group_by_tag().items():
            print(f"\nТег: {tag}")
            print_records(records)
        return False

    def show_birthdays(self):
        """Контакти, у яких день народження через задану кількість днів."""
        raw = read_line("Через скільки днів (0 — сьогодні): ").strip()
        if not raw.isdigit():
            raise ValueError("Введіть ціле число днів, 0 або більше.")
        found = self.contacts.upcoming_birthdays(int(raw))
        if found:
            print_records(found)
        else:
            print(f"Немає контактів, у яких день народження через {raw} дн.")
        return False

    # ----- Нотатки -----

    def get_contact(self, full_name):
        """Знаходить контакт за ім'ям або повідомляє, що його немає."""
        record = self.contacts.find(full_name)
        if record is None:
            raise ValueError("Контакт з таким ім'ям не знайдено.")
        return record

    def ask_note(self):
        """Питає номер нотатки і повертає її."""
        raw = read_line("Номер нотатки: ").strip()
        if not raw.isdigit():
            raise ValueError("Номер нотатки має бути числом.")
        note = self.notes.find(int(raw))
        if note is None:
            raise ValueError("Нотатку з таким номером не знайдено.")
        return note

    def add_note(self):
        """Створює нотатку з перевіреними полями і за бажанням прив'язує її."""
        title = ask_field("Заголовок", Title)
        text = ask_field("Текст нотатки", NoteText)
        tags = ask_field("Теги з # (наприклад, #робота #ідеї)", NoteTags,
                         "пропустити")
        contact_name = None
        link = read_line(
            "Ім'я контакту для прив'язки (Enter — без прив'язки): "
        )
        if link.strip():
            contact_name = self.get_contact(link).full_name
        note = self.notes.add(title, text, tags, contact_name)
        print("Нотатку додано:")
        print(note)
        return True

    def show_notes(self):
        if not self.notes:
            print("Нотаток ще немає.")
            return False
        print_notes(self.notes.values())
        return False

    def edit_note(self):
        """Змінює одне поле нотатки або прив'язку до контакту."""
        note = self.ask_note()
        print(note)
        print("  1. Заголовок")
        print("  2. Текст")
        print("  3. Теги")
        print("  4. Прив'язка до контакту")
        choice = read_line("Номер поля (Enter — скасувати): ").strip()
        if not choice:
            return False
        if choice == "4":
            link = read_line(
                "Ім'я контакту (Enter — без змін, «-» — відв'язати): "
            )
            link = link.strip()
            if not link:
                print("Поле не змінено.")
                return False
            note.contact_name = None if link == "-" else (
                self.get_contact(link).full_name)
        else:
            field, label, field_class = pick_by_number(NOTE_FIELDS, choice)
            new_value = ask_field(f"Нове значення для «{label}»", field_class,
                                  "без змін")
            if new_value is None:
                print("Поле не змінено.")
                return False
            note.update(field, new_value)
        print("Нотатку оновлено.")
        return True

    def delete_note(self):
        note = self.ask_note()
        if not confirm(f"Видалити нотатку «{note.title}»?"):
            print("Видалення скасовано.")
            return False
        del self.notes[note.note_id]
        print("Нотатку видалено.")
        return True

    def search_notes(self):
        query = read_line("Що шукаємо в нотатках: ").strip()
        if not query:
            raise ValueError("Пошуковий запит не може бути порожнім.")
        found = self.notes.search(query)
        if found:
            print_notes(found)
        else:
            print("Нічого не знайдено.")
        return False

    def find_notes_by_tag(self):
        """Нотатки з одним конкретним тегом."""
        raw = read_line("Тег для пошуку (наприклад, #робота): ")
        tags = NoteTags(raw).value or []
        if len(tags) != 1:
            raise ValueError("Введіть один тег, наприклад #робота.")
        found = self.notes.find_by_tag(tags[0])
        if found:
            print_notes(found)
        else:
            print(f"Нотаток з тегом {tags[0]} немає.")
        return False

    def sort_notes(self):
        """Виводить нотатки, згруповані за тегами."""
        if not self.notes:
            print("Нотаток ще немає.")
            return False
        for tag, notes in self.notes.group_by_tags().items():
            print(f"\n{tag} ({len(notes)})")
            print_notes(notes)
        return False

    def show_contact_notes(self):
        record = self.ask_contact()
        found = self.notes.find_by_contact(record.full_name)
        if found:
            print_notes(found)
        else:
            print(f"Нотаток для контакту {record.full_name} немає.")
        return False

    def show_help(self):
        """Довідка, розділена на контакти, нотатки і загальні команди."""
        # Зворотна таблиця: повна назва -> її скорочення
        short_names = {}
        for short, full in ALIASES.items():
            short_names.setdefault(full, []).append(short)

        sections = [
            ("Контакти", [
                "add-contact", "contacts", "edit-contact", "delete-contact",
                "search-contact", "sort-contacts", "birthdays",
            ]),
            ("Нотатки", [
                "add-note", "notes", "edit-note", "delete-note",
                "search-note", "find-tag", "sort-notes", "contact-notes",
            ]),
            ("Загальні", ["help"]),
        ]
        print("Доступні команди (у дужках — скорочення):")
        for title, commands in sections:
            print(f"\n{title}:")
            for command in commands:
                description = self.commands[command][0]
                shorts = ", ".join(short_names.get(command, []))
                label = f"{command} ({shorts})"
                print(f"  {label:<30} {description}")
        print("\nВихід з програми: exit (q)")
        return False


def main():
    """Точка входу. Файл даних можна задати змінною PA_DATA_FILE."""
    data_file = os.environ.get("PA_DATA_FILE", DATA_FILE)
    try:
        assistant = PersonalAssistant(data_file)
    except ValueError as error:
        print(f"Помилка: {error}")
        sys.exit(1)
    assistant.run()

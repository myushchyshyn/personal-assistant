"""Контакти: запис з полями (композиція) та адресна книга.

Адресна книга зберігає записи за ключем «ім'я прізвище» у нижньому регістрі.
Вона вміє шукати контакти, групувати їх за тегом і знаходити дні народження.
"""

from collections import UserDict, defaultdict
from datetime import date

from .colors import paint_tag
from .fields import (
    Address,
    Birthday,
    ContactTag,
    Email,
    FirstName,
    LastName,
    Phone,
)

# Поля, які можна змінювати після створення контакту
EDITABLE_FIELDS = {
    "first_name": FirstName,
    "last_name": LastName,
    "address": Address,
    "phone": Phone,
    "tag": ContactTag,
    "email": Email,
    "birthday": Birthday,
}


class Record:
    """Запис одного контакту. Складається з окремих полів-об'єктів."""

    def __init__(self, first_name, last_name, address, phone, tag,
                 email=None, birthday=None):
        # Кожне значення перевіряється відповідним полем
        self.first_name = FirstName(first_name)
        self.last_name = LastName(last_name)
        self.address = Address(address)
        self.phone = Phone(phone)
        self.tag = ContactTag(tag)
        self.email = Email(email)
        self.birthday = Birthday(birthday)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def key(self):
        """Ключ запису в адресній книзі (без урахування регістру)."""
        return self.full_name.lower()

    def update(self, field, raw_value):
        """Замінює одне поле запису на нове значення після перевірки."""
        if field not in EDITABLE_FIELDS:
            raise ValueError("Такого поля контакту немає.")
        setattr(self, field, EDITABLE_FIELDS[field](raw_value))

    def matches(self, query):
        """Чи є query у будь-якому полі контакту (без урахування регістру)."""
        query = query.lower()
        fields = [
            self.first_name, self.last_name, self.address,
            self.phone, self.email, self.birthday, self.tag,
        ]
        texts = [str(field) for field in fields]
        # Окремо шукаємо і за цифрами номера, щоб «0501234567» теж знаходив
        texts.append(str(self.phone.value))
        return any(query in text.lower() for text in texts)

    def __str__(self):
        return (
            f"Ім'я: {self.full_name}\n"
            f"  Адреса: {self.address}\n"
            f"  Телефон: {self.phone}\n"
            f"  Email: {str(self.email) or '-'}\n"
            f"  День народження: {str(self.birthday) or '-'}\n"
            f"  Тег: {paint_tag(str(self.tag))}"
        )


class AddressBook(UserDict):
    """Адресна книга: контакти за ключем, пошук, групування, привітання."""

    def add_record(self, record):
        if record.key in self.data:
            raise ValueError("Контакт з таким ім'ям і прізвищем уже існує.")
        self.data[record.key] = record

    def find(self, full_name):
        """Повертає запис за повним ім'ям або None, якщо його немає."""
        return self.data.get(full_name.strip().lower())

    def rebuild_keys(self):
        """Оновлює ключі всіх записів після зміни імені контакту."""
        self.data = {record.key: record for record in self.data.values()}

    def search(self, query):
        """Контакти, у яких будь-яке поле містить query."""
        return [record for record in self.data.values()
                if record.matches(query)]

    def group_by_tag(self):
        """Групує контакти за тегом. Теги виводяться в алфавітному порядку."""
        # defaultdict створює порожній список для нового тегу автоматично
        groups = defaultdict(list)
        for record in self.data.values():
            groups[record.tag.value].append(record)
        return {tag: groups[tag] for tag in sorted(groups)}

    def upcoming_birthdays(self, days, today=None):
        """Контакти, у яких день народження рівно через days днів від today."""
        today = today or date.today()
        return [
            record for record in self.data.values()
            if record.birthday.value is not None
            and record.birthday.days_until(today) == days
        ]

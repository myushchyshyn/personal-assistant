"""Поля контакту та нотатки з валідацією введених даних.

Кожне поле перевіряє значення під час створення. Якщо значення некоректне,
піднімається ValueError з поясненням для користувача.
"""

import re
from datetime import date, datetime

# Шаблон телефону, який показується користувачу
PHONE_TEMPLATE = "+380(XX)XXX-XX-XX"
PHONE_COUNTRY_CODE = "380"
# Символ, яким користувач прибирає необов'язкове значення
CLEAR_MARK = "-"
BIRTHDAY_FORMAT = "%d.%m.%Y"

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Ім'я: літери (українські та латинські), можливі пробіл, дефіс і апостроф
NAME_PATTERN = re.compile(r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*")
# Тег нотатки: символ # і далі літери, цифри або підкреслення
NOTE_TAG_PATTERN = re.compile(r"#\w+")


class Field:
    """Базовий клас поля: зберігає значення, яке пройшло перевірку."""

    optional = False

    def __init__(self, raw_value):
        # validate() перевіряє значення і повертає його у потрібному вигляді
        self.value = self.validate(raw_value)

    def validate(self, raw_value):
        """Перевіряє значення. У нащадках перевизначається."""
        return raw_value

    def __str__(self):
        return "" if self.value is None else str(self.value)


class OptionalField(Field):
    """Необов'язкове поле: порожній ввід або «-» означає, що значення немає."""

    optional = True

    def validate(self, raw_value):
        text = "" if raw_value is None else raw_value.strip()
        if text in ("", CLEAR_MARK):
            return None
        return self.parse(text)

    def parse(self, text):
        """Перевіряє непорожній текст. У нащадках перевизначається."""
        raise NotImplementedError


class TextField(Field):
    """Обов'язковий текст, який не може бути порожнім."""

    label = "Текст"

    def validate(self, raw_value):
        text = raw_value.strip()
        if not text:
            raise ValueError(f"Поле «{self.label}» не може бути порожнім.")
        return text


class Name(TextField):
    """Ім'я або прізвище: лише літери, можливі пробіл, дефіс і апостроф."""

    def validate(self, raw_value):
        text = super().validate(raw_value)
        if not NAME_PATTERN.fullmatch(text):
            raise ValueError(
                f"«{self.label}» має містити лише літери "
                "(можна пробіл, дефіс або апостроф)."
            )
        return text


class FirstName(Name):
    """Ім'я контакту."""

    label = "Ім'я"


class LastName(Name):
    """Прізвище контакту."""

    label = "Прізвище"


class Address(TextField):
    """Адреса контакту."""

    label = "Адреса"


class ContactTag(TextField):
    """Тег контакту для групування: одне слово без пробілів."""

    label = "Тег"

    def validate(self, raw_value):
        text = super().validate(raw_value)
        if len(text.split()) != 1:
            raise ValueError("Тег має бути одним словом без пробілів.")
        # Нижній регістр, щоб «Робота» і «робота» потрапили в одну групу
        return text.lower()


def normalize_phone(raw_value):
    """Приводить номер до вигляду 380XXXXXXXXX (лише цифри)."""
    digits = re.sub(r"\D", "", raw_value)
    # 9 цифр — це номер після +380, код країни додаємо автоматично
    if len(digits) == 9:
        digits = PHONE_COUNTRY_CODE + digits
    # Номер у форматі 0XXXXXXXXX: замінюємо нуль на код країни
    elif len(digits) == 10 and digits.startswith("0"):
        digits = PHONE_COUNTRY_CODE + digits[1:]
    if len(digits) != 12 or not digits.startswith(PHONE_COUNTRY_CODE):
        raise ValueError(
            f"Некоректний номер. Використовуйте формат {PHONE_TEMPLATE}."
        )
    return digits


def format_phone(digits):
    """Форматує номер 380XXXXXXXXX у вигляд +380(XX)XXX-XX-XX."""
    return (
        f"+{digits[:3]}({digits[3:5]}){digits[5:8]}"
        f"-{digits[8:10]}-{digits[10:12]}"
    )


class Phone(Field):
    """Телефон у міжнародному форматі. Зберігається як 12 цифр."""

    label = "Телефон"

    def validate(self, raw_value):
        return normalize_phone(raw_value)

    def __str__(self):
        return format_phone(self.value)


class Email(OptionalField):
    """Електронна пошта, необов'язкова."""

    def parse(self, text):
        if not EMAIL_PATTERN.fullmatch(text):
            raise ValueError("Некоректний email. Приклад: name@example.com")
        return text


class Birthday(OptionalField):
    """День народження у форматі ДД.ММ.РРРР, необов'язковий."""

    def parse(self, text):
        try:
            value = datetime.strptime(text, BIRTHDAY_FORMAT).date()
        except ValueError:
            raise ValueError(
                "Некоректна дата. Формат: ДД.ММ.РРРР, наприклад 05.03.1990."
            ) from None
        if value > date.today():
            raise ValueError("Дата народження не може бути в майбутньому.")
        return value

    def __str__(self):
        if self.value is None:
            return ""
        return self.value.strftime(BIRTHDAY_FORMAT)

    def next_occurrence(self, today):
        """Найближча дата дня народження, яка не раніша за today."""
        for year in (today.year, today.year + 1):
            try:
                candidate = self.value.replace(year=year)
            except ValueError:  # 29 лютого в рік без 29 лютого
                candidate = date(year, 3, 1)
            if candidate >= today:
                return candidate

    def days_until(self, today):
        """Кількість днів від today до найближчого дня народження."""
        return (self.next_occurrence(today) - today).days


class NoteTags(OptionalField):
    """Теги нотатки: слова з # на початку, наприклад «#робота #ідеї»."""

    def parse(self, text):
        tags = []
        for token in text.split():
            if not NOTE_TAG_PATTERN.fullmatch(token):
                raise ValueError(
                    f"Тег «{token}» має починатися з # і містити лише "
                    "літери, цифри або підкреслення."
                )
            tag = token.lower()
            if tag not in tags:
                tags.append(tag)
        return tags

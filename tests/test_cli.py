"""Тести командного циклу: введення з клавіатури підміняється списком."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from personal_assistant.cli import PersonalAssistant, fix_encoding


def run_session(answers, data_file):
    """Запускає застосунок, подаючи answers замість введення з клавіатури."""
    assistant = PersonalAssistant(data_file)
    output = io.StringIO()
    with mock.patch("builtins.input", side_effect=answers), \
            contextlib.redirect_stdout(output):
        assistant.run()
    return assistant, output.getvalue()


class FixEncodingTests(unittest.TestCase):
    def test_utf8_text_is_unchanged(self):
        self.assertEqual(fix_encoding("вул. Бальзака 61"), "вул. Бальзака 61")

    def test_cp1251_bytes_are_decoded(self):
        # Термінал надіслав cp1251: байти читаються як сурогати
        raw = "вул. Бальзака".encode("cp1251")
        text = raw.decode("utf-8", "surrogateescape")
        self.assertEqual(fix_encoding(text), "вул. Бальзака")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.pkl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_contact_retries_invalid_input(self):
        answers = [
            "add-contact",
            "Анна", "Коваль", "Київ",
            "123",                      # некоректний телефон — повтор
            "0501234567",
            "робота",
            "anna@example",             # некоректний email — повтор
            "",                         # email пропущено
            "05.03.1990",
            "exit",
        ]
        assistant, output = run_session(answers, self.data_file)
        self.assertIn("Некоректний номер", output)
        self.assertIn("Некоректний email", output)
        record = assistant.contacts.find("Анна Коваль")
        self.assertEqual(str(record.phone), "+380(50)123-45-67")
        self.assertIsNone(record.email.value)

    def test_data_is_saved_and_loaded_after_restart(self):
        answers = [
            "add-note", "План", "Купити молоко", "#побут", "",
            "exit",
        ]
        run_session(answers, self.data_file)
        assistant, output = run_session(["notes", "exit"], self.data_file)
        self.assertIn("Купити молоко", output)

    def test_short_aliases_work_like_full_commands(self):
        # a — скорочення add-contact, q — скорочення exit
        answers = [
            "a", "Анна", "Коваль", "Київ", "0501234567", "друзі",
            "", "", "q",
        ]
        assistant, output = run_session(answers, self.data_file)
        self.assertIsNotNone(assistant.contacts.find("Анна Коваль"))
        self.assertIn("До побачення", output)

    def test_bad_terminal_bytes_do_not_stop_program(self):
        # Некоректні байти з терміналу мають дати повідомлення, а не падіння
        bad_bytes = UnicodeDecodeError("utf-8", b"\xd1", 0, 1, "invalid")
        _, output = run_session([bad_bytes, "exit"], self.data_file)
        self.assertIn("кодуванні UTF-8", output)
        self.assertIn("До побачення", output)

    def test_unknown_command_does_not_stop_program(self):
        _, output = run_session(["абракадабра", "help", "exit"],
                                self.data_file)
        self.assertIn("Невідома команда", output)
        self.assertIn("Доступні команди", output)


if __name__ == "__main__":
    unittest.main()

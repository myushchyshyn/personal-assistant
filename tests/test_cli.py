"""Тести командного циклу: введення з клавіатури підміняється списком."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from personal_assistant.cli import PersonalAssistant


def run_session(answers, data_file):
    """Запускає застосунок, подаючи answers замість введення з клавіатури."""
    assistant = PersonalAssistant(data_file)
    output = io.StringIO()
    with mock.patch("builtins.input", side_effect=answers), \
            contextlib.redirect_stdout(output):
        assistant.run()
    return assistant, output.getvalue()


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

    def test_unknown_command_does_not_stop_program(self):
        _, output = run_session(["абракадабра", "help", "exit"],
                                self.data_file)
        self.assertIn("Невідома команда", output)
        self.assertIn("Доступні команди", output)


if __name__ == "__main__":
    unittest.main()

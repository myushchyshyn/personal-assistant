"""Кольоровий вивід тегів у терміналі."""

import os
import sys

BLUE = "\033[34m"
RESET = "\033[0m"


def paint_tag(text):
    """Фарбує текст тегу в синій колір, якщо вивід іде в термінал.

    Колір вимикається, коли вивід перенаправлено у файл або задано
    змінну NO_COLOR (стандарт no-color.org).
    """
    if "NO_COLOR" in os.environ or not sys.stdout.isatty():
        return text
    return f"{BLUE}{text}{RESET}"

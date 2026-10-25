"""Збереження контактів і нотаток на диск за допомогою pickle."""

import pickle
from pathlib import Path

from .contacts import AddressBook
from .notes import NoteBook

DATA_DIR = Path.home() / ".personal_assistant"
DATA_FILE = DATA_DIR / "data.pkl"


def save_data(contacts, notes, path=DATA_FILE):
    """Записує контакти й нотатки у файл.

    Спочатку пишемо у тимчасовий файл, а потім замінюємо основний.
    Так збій посеред запису не псує вже збережені дані.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "wb") as file:
        pickle.dump({"contacts": contacts, "notes": notes}, file)
    tmp_path.replace(path)


def load_data(path=DATA_FILE):
    """Читає дані з файлу. Якщо файлу ще немає — повертає порожні книги."""
    try:
        with open(path, "rb") as file:
            data = pickle.load(file)
    except FileNotFoundError:
        return AddressBook(), NoteBook()
    except (pickle.UnpicklingError, EOFError, AttributeError) as error:
        raise ValueError(f"Файл даних пошкоджено: {path} ({error})") from None
    return data["contacts"], data["notes"]

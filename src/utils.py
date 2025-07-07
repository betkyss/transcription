import os
import re
import shutil
from rich.console import Console

console = Console(stderr=True, record=True)

def sanitize_filename(filename):
    """
    Очищает имя файла от недопустимых символов.
    """
    return re.sub(r'[\\/*?:"<>|]',"", filename)

def ensure_dir_exists(path):
    """
    Убеждается, что директория существует.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def cleanup_temp_files(*files):
    """
    Удаляет временные файлы.
    """
    console.print("\n[bold cyan]Очистка временных файлов...[/bold cyan]")
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                console.print(f"[dim]Удален временный файл:[/] {file_path}")
            except OSError as e:
                console.print(f"[red]Ошибка при удалении {file_path}:[/] {e}")


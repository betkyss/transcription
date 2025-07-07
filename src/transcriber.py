import os
import whisper
import contextlib
from rich.console import Console
from .utils import ensure_dir_exists, sanitize_filename

console = Console(stderr=True, record=True)

def transcribe_audio(audio_file_path, video_title, output_dir="transcriptions", status=None):
    """
    Транскрибирует аудиофайл, обновляя текстовый статус.
    """
    ensure_dir_exists(output_dir)
    safe_video_title = sanitize_filename(video_title)
    output_filepath = os.path.join(output_dir, f"{safe_video_title}.txt")

    def update_status(message):
        if status:
            status.update(f"[cyan]{message}")

    update_status("Загрузка модели Whisper (base)...")
    try:
        model = whisper.load_model("base")
    except Exception as e:
        console.print(f"\n[bold red]Ошибка при загрузке модели Whisper:[/bold red] {e}")
        if status:
            status.update("[red]Ошибка модели")
        return

    update_status("Обработка аудио (это может занять время)...")
    
    try:
        # Подавляем стандартный вывод Whisper
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                result = model.transcribe(audio_file_path, fp16=False, verbose=False)
        
        update_status("Сохранение транскрипции...")
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(result['text'].strip())

        if status:
            status.update("[green]Транскрипция завершена.")
        console.print(f"\n[bold green]Транскрипция сохранена в файл:[/] [cyan]{output_filepath}[/cyan]")

    except Exception as e:
        console.print(f"\n[bold red]Ошибка во время транскрипции:[/bold red] {e}")
        if status:
            status.update("[red]Ошибка транскрипции")


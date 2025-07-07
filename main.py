import sys
import warnings
from rich.console import Console

# Игнорируем FutureWarning от torch.load внутри whisper
warnings.filterwarnings("ignore", category=FutureWarning, module='torch.serialization')

from src.downloader import download_audio
from src.transcriber import transcribe_audio
from src.utils import cleanup_temp_files

console = Console(stderr=True, record=True)

def main():
    """
    Главная функция.
    """
    audio_file_path = None
    try:
        url = console.input("[bold cyan]Введите URL YouTube видео:[/bold cyan] ")
        if not url:
            console.print("[red]URL не может быть пустым.[/red]")
            sys.exit(1)

        with console.status("[bold green]Выполняется...") as status:
            # 1. Скачивание аудио
            audio_file_path, video_title = download_audio(
                url,
                temp_dir="temp",
                status=status
            )

            if not audio_file_path or not video_title:
                console.print("[red]Не удалось скачать аудио. Прерывание.[/red]")
                sys.exit(1)

            # 2. Транскрибация
            transcribe_audio(
                audio_file_path,
                video_title,
                output_dir="transcriptions",
                status=status
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Процесс прерван пользователем.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Произошла непредвиденная ошибка:[/bold red] {e}")
        sys.exit(1)
    finally:
        # 3. Очистка
        if audio_file_path:
            cleanup_temp_files(audio_file_path)

if __name__ == "__main__":
    main()

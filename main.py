import sys
import os
import warnings
from rich.console import Console
from rich.prompt import Prompt

# Игнорируем FutureWarning от torch.load внутри whisper
warnings.filterwarnings("ignore", category=FutureWarning, module='torch.serialization')

from src.downloader import download_audio, extract_audio_from_local_file
from src.transcriber import transcribe_audio
from src.utils import cleanup_temp_files, ensure_dir_exists

console = Console(stderr=True, record=True)

def handle_youtube_url():
    """Обработка URL с YouTube."""
    url = console.input("[bold cyan]Введите URL YouTube видео:[/bold cyan] ")
    if not url:
        console.print("[red]URL не может быть пустым.[/red]")
        return None, None
    
    with console.status("[bold green]Выполняется...") as status:
        return download_audio(url, temp_dir="temp", status=status)

def handle_local_file():
    """Отображает файлы из папки 'videos' и обрабатывает выбор пользователя."""
    videos_dir = "videos"
    ensure_dir_exists(videos_dir)
    
    files = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp3', '.mp4'))]
    
    if not files:
        console.print(f"[yellow]Папка '{videos_dir}' пуста.[/yellow]")
        console.print("Пожалуйста, добавьте в нее файлы .mp3 или .mp4 и попробуйте снова.")
        return None, None

    console.print("\n[bold magenta]Выберите файл для транскрибации:[/bold magenta]")
    for i, filename in enumerate(files):
        console.print(f"  [{i+1}] {filename}")
    console.print(f"  [{len(files)+1}] Назад в главное меню")

    choice = Prompt.ask(
        "Введите номер файла", 
        choices=[str(i) for i in range(1, len(files) + 2)],
        show_choices=False
    )
    
    choice_idx = int(choice) - 1

    if choice_idx == len(files): # Опция "Назад"
        return None, None

    file_path = os.path.join(videos_dir, files[choice_idx])
    video_title = os.path.splitext(files[choice_idx])[0]
    temp_dir = "temp"
    
    with console.status("[bold green]Обработка файла...") as status:
        if file_path.lower().endswith('.mp3'):
            status.update("[cyan]Копирование файла...")
            temp_audio_path = os.path.join(temp_dir, os.path.basename(file_path))
            import shutil
            shutil.copy(file_path, temp_audio_path)
            return temp_audio_path, video_title
        
        elif file_path.lower().endswith('.mp4'):
            return extract_audio_from_local_file(file_path, temp_dir, status)
    
    return None, None # На случай непредвиденных обстоятельств

def main():
    """
    Главная функция.
    """
    while True:
        audio_file_path = None
        video_title = None
        
        try:
            console.print("\n[bold magenta]Выберите источник для транскрибации:[/bold magenta]")
            choice = Prompt.ask(
                "  [1] Локальный файл из папки 'videos'\n"
                "  [2] URL с YouTube\n"
                "  [3] Выход",
                choices=["1", "2", "3"],
                default="1"
            )

            if choice == "1":
                audio_file_path, video_title = handle_local_file()
            elif choice == "2":
                audio_file_path, video_title = handle_youtube_url()
            elif choice == "3":
                console.print("[yellow]Выход.[/yellow]")
                sys.exit(0)

            if not audio_file_path or not video_title:
                # Пользователь выбрал "Назад" или произошла ошибка
                continue

            # Транскрибация
            with console.status("[bold green]Выполняется...") as status:
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
            # Очистка
            if audio_file_path:
                cleanup_temp_files(audio_file_path)

if __name__ == "__main__":
    main()

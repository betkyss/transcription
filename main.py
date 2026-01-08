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
    """Отображает файлы из папки 'videos' и обрабатывает множественный выбор пользователя."""
    videos_dir = "videos"
    ensure_dir_exists(videos_dir)
    
    files = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp3', '.mp4'))]
    
    if not files:
        console.print(f"[yellow]Папка '{videos_dir}' пуста.[/yellow]")
        console.print("Пожалуйста, добавьте в нее файлы .mp3 или .mp4 и попробуйте снова.")
        return []

    selected = [False] * len(files)

    while True:
        console.print("\n[bold magenta]Выберите файлы для транскрибации (введите номер для выбора/отмены):[/bold magenta]")
        
        for i, filename in enumerate(files):
            marker = "*" if selected[i] else " "
            console.print(f"  [{marker}] {i+1}. {filename}")

        console.print("-" * 30)
        console.print("  [A] Выбрать/снять все")
        console.print("  [T] Транскрибировать выбранные")
        console.print("  [B] Назад в главное меню")

        choice = Prompt.ask("[bold cyan]Ваш выбор?[/bold cyan]", show_choices=False).lower()

        if choice == 'b':
            return []
        
        if choice == 't':
            selected_files = [os.path.join(videos_dir, files[i]) for i, s in enumerate(selected) if s]
            if not selected_files:
                console.print("[yellow]Файлы не выбраны. Нажмите 'b' для возврата.[/yellow]")
                continue
            return selected_files

        if choice == 'a':
            if all(selected):
                selected = [False] * len(files)
            else:
                selected = [True] * len(files)
            continue

        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(files):
                selected[choice_idx] = not selected[choice_idx]
            else:
                console.print(f"[red]Неверный номер. Введите число от 1 до {len(files)}.[/red]")
        except ValueError:
            console.print("[red]Неверный ввод. Пожалуйста, введите номер или букву опции.[/red]")

def main():
    """
    Главная функция.
    """
    while True:
        try:
            console.print("\n[bold magenta]Выберите источник для транскрибации:[/bold magenta]")
            choice = Prompt.ask(
                "  [1] Локальный файл из папки 'videos'\n"
                "  [2] URL с YouTube\n"
                "  [3] Выход",
                choices=["1", "2", "3"],
                default="1"
            )

            files_to_process = []
            if choice == "1":
                # handle_local_file теперь возвращает список путей
                local_files = handle_local_file()
                for file_path in local_files:
                    files_to_process.append(file_path)
            
            elif choice == "2":
                # handle_youtube_url возвращает один путь к аудио и заголовок
                # Мы не можем смешивать их в одном пакете, поэтому обработаем его отдельно
                audio_file_path, video_title = handle_youtube_url()
                if audio_file_path and video_title:
                    # Транскрибация для одного YouTube URL
                    with console.status("[bold green]Выполняется...") as status:
                        transcribe_audio(
                            audio_file_path,
                            video_title,
                            output_dir="transcriptions",
                            status=status
                        )
                    cleanup_temp_files(audio_file_path)
                continue # Возвращаемся в главное меню после обработки URL

            elif choice == "3":
                console.print("[yellow]Выход.[/yellow]")
                sys.exit(0)

            # Пакетная обработка локальных файлов
            if not files_to_process:
                continue

            console.print(f"\n[bold green]Начинается пакетная обработка {len(files_to_process)} файлов...[/bold green]")
            for file_path in files_to_process:
                audio_file_path = None
                video_title = os.path.splitext(os.path.basename(file_path))[0]
                temp_dir = "temp"
                
                console.print(f"\n[cyan]Обработка файла: {os.path.basename(file_path)}[/cyan]")
                try:
                    with console.status("[bold green]Подготовка аудио...") as status:
                        if file_path.lower().endswith('.mp3'):
                            status.update("[cyan]Копирование файла...")
                            temp_audio_path = os.path.join(temp_dir, os.path.basename(file_path))
                            import shutil
                            shutil.copy(file_path, temp_audio_path)
                            audio_file_path = temp_audio_path
                        
                        elif file_path.lower().endswith('.mp4'):
                            audio_file_path, _ = extract_audio_from_local_file(file_path, temp_dir, status)

                    if not audio_file_path:
                        console.print(f"[red]Не удалось извлечь аудио из {os.path.basename(file_path)}[/red]")
                        continue
                    
                    # Транскрибация
                    with console.status("[bold green]Транскрибация...") as status:
                        transcribe_audio(
                            audio_file_path,
                            video_title,
                            output_dir="transcriptions",
                            status=status
                        )

                except Exception as e:
                    console.print(f"\n[bold red]Ошибка при обработке файла {os.path.basename(file_path)}:[/bold red] {e}")
                finally:
                    if audio_file_path:
                        cleanup_temp_files(audio_file_path)
            
            console.print("\n[bold green]Пакетная обработка завершена.[/bold green]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Процесс прерван пользователем.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[bold red]Произошла непредвиденная ошибка:[/bold red] {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()

import os
import sys
import time
from threading import Event, Thread
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

from src.downloader import download_audio, extract_audio_from_local_file
from src.utils import cleanup_temp_files, ensure_dir_exists, sanitize_filename

try:
    # Official OpenAI Python SDK (>=1.0)
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


console = Console(stderr=True, record=True)

# Load variables from .env (does not override already set env)
load_dotenv()


def _get_openai_client() -> "OpenAI":
    """Create and return an OpenAI client using env vars.

    Requires `OPENAI_API_KEY`. Optionally honors `OPENAI_BASE_URL` for proxies/self-hosted gateways.
    """
    if OpenAI is None:
        raise RuntimeError(
            "Пакет 'openai' не установлен. Добавьте его в окружение (pip install openai)."
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не найден переменная окружения OPENAI_API_KEY. Установите ключ API: \n"
            "  export OPENAI_API_KEY=your_key_here"
        )

    base_url = os.getenv("OPENAI_BASE_URL")

    # Request timeout in seconds (applies to connect+read+write)
    # Default to 600s to avoid silent long hangs; can be overridden via env.
    try:
        timeout_s = float(os.getenv("OPENAI_TIMEOUT", os.getenv("OPENAI_REQUEST_TIMEOUT", "600")))
    except ValueError:
        timeout_s = 600.0

    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s)
    return OpenAI(api_key=api_key, timeout=timeout_s)


def transcribe_audio_api(
    audio_file_path: str,
    video_title: str,
    output_dir: str = "transcriptions",
    status=None,
    *,
    model: Optional[str] = None,
    language: Optional[str] = None,
) -> None:
    """Transcribe audio via OpenAI API and save to text file.

    - `model`: override via arg or `OPENAI_TRANSCRIBE_MODEL` (defaults to 'whisper-1').
    - `language`: optional language hint (e.g., 'ru').
    """
    ensure_dir_exists(output_dir)
    safe_title = sanitize_filename(video_title)
    out_path = os.path.join(output_dir, f"{safe_title}.txt")

    def update(msg: str):
        if status:
            status.update(f"[cyan]{msg}")

    model_name = model or os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

    # Pre-flight info
    try:
        file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
    except OSError:
        file_size_mb = 0.0
    update(f"Отправка в OpenAI API (model={model_name}, файл ~{file_size_mb:.2f} MB)...")

    try:
        client = _get_openai_client()
    except Exception as e:
        console.print(f"\n[bold red]Ошибка клиента OpenAI:[/bold red] {e}")
        if status:
            status.update("[red]Ошибка клиента OpenAI")
        return

    # Heartbeat thread to show progress while waiting for API
    stop_hb = Event()

    def _heartbeat():
        start = time.time()
        tick = 0
        while not stop_hb.wait(10.0):
            tick += 1
            elapsed = int(time.time() - start)
            # Log a periodic "still working" message so it's clear we're alive
            console.log(
                f"[dim]Транскрибация идет... прошло {elapsed} сек (попытка {tick}).[/dim]"
            )

    hb_thread: Optional[Thread] = None
    try:
        hb_thread = Thread(target=_heartbeat, daemon=True)
        hb_thread.start()

        with open(audio_file_path, "rb") as f:
            # New SDK path: client.audio.transcriptions.create
            kwargs = {"model": model_name, "file": f}
            if language:
                kwargs["language"] = language
            transcript = client.audio.transcriptions.create(**kwargs)

        update("Сохранение транскрипции...")
        text = getattr(transcript, "text", None)
        if not text:
            # Fallback: best-effort stringify the response
            text = str(transcript)

        with open(out_path, "w", encoding="utf-8") as fp:
            fp.write(text.strip())

        if status:
            status.update("[green]Транскрипция завершена.")
        console.print(f"\n[bold green]Транскрипция сохранена:[/] [cyan]{out_path}[/cyan]")

    except Exception as e:
        console.print(f"\n[bold red]Ошибка при транскрибации через API:[/bold red] {e}")
        if status:
            status.update("[red]Ошибка транскрипции API")
    finally:
        # Stop heartbeat regardless of success/failure
        stop_hb.set()
        if hb_thread is not None:
            hb_thread.join(timeout=0.1)


def handle_youtube_url():
    url = console.input("[bold cyan]Введите URL YouTube видео:[/bold cyan] ")
    if not url:
        console.print("[red]URL не может быть пустым.[/red]")
        return None, None

    with console.status("[bold green]Выполняется...") as status:
        temp_dir = os.getenv("TEMP_DIR", "temp")
        return download_audio(url, temp_dir=temp_dir, status=status)


def handle_local_file():
    """Отображает файлы из папки 'videos' и позволяет выбрать несколько."""
    videos_dir = os.getenv("VIDEOS_DIR", "videos")
    ensure_dir_exists(videos_dir)

    files = [f for f in os.listdir(videos_dir) if f.lower().endswith((".mp3", ".mp4"))]
    if not files:
        console.print(f"[yellow]Папка '{videos_dir}' пуста.[/yellow]")
        console.print("Добавьте файлы .mp3 или .mp4 и попробуйте снова.")
        return []

    selected = [False] * len(files)
    while True:
        console.print("\n[bold magenta]Выберите файлы для транскрибации (API):[/bold magenta]")
        for i, filename in enumerate(files):
            marker = "*" if selected[i] else " "
            console.print(f"  [{marker}] {i+1}. {filename}")

        console.print("-" * 30)
        console.print("  [A] Выбрать/снять все")
        console.print("  [T] Транскрибировать выбранные")
        console.print("  [B] Назад в главное меню")

        choice = Prompt.ask("[bold cyan]Ваш выбор?[/bold cyan]", show_choices=False).lower()

        if choice == "b":
            return []
        if choice == "t":
            return [os.path.join(videos_dir, files[i]) for i, s in enumerate(selected) if s]
        if choice == "a":
            selected = [not all(selected)] * len(files) if files else selected
            continue
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                selected[idx] = not selected[idx]
            else:
                console.print(f"[red]Неверный номер. 1..{len(files)}[/red]")
        except ValueError:
            console.print("[red]Неверный ввод. Номер или буква опции.[/red]")


def main():
    # Optional defaults via env vars
    default_model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    default_lang = os.getenv("OPENAI_TRANSCRIBE_LANG")  # e.g., 'ru'
    transcriptions_dir = os.getenv("TRANSCRIPTIONS_DIR", "transcriptions")
    temp_dir_from_env = os.getenv("TEMP_DIR", "temp")

    while True:
        try:
            console.print("\n[bold magenta]Источник для транскрибации (API):[/bold magenta]")
            choice = Prompt.ask(
                "  [1] Локальный файл из 'videos'\n"
                "  [2] URL с YouTube\n"
                "  [3] Выход",
                choices=["1", "2", "3"],
                default="1",
            )

            files_to_process = []

            if choice == "1":
                for f in handle_local_file():
                    files_to_process.append(f)

            elif choice == "2":
                audio_file_path, video_title = handle_youtube_url()
                if audio_file_path and video_title:
                    with console.status("[bold green]Выполняется...") as status:
                        transcribe_audio_api(
                            audio_file_path,
                            video_title,
                            output_dir=transcriptions_dir,
                            status=status,
                            model=default_model,
                            language=default_lang,
                        )
                    cleanup_temp_files(audio_file_path)
                continue

            elif choice == "3":
                console.print("[yellow]Выход.[/yellow]")
                sys.exit(0)

            if not files_to_process:
                continue

            console.print(
                f"\n[bold green]Начинается пакетная обработка {len(files_to_process)} файлов (API)...[/bold green]"
            )

            for file_path in files_to_process:
                audio_file_path = None
                video_title = os.path.splitext(os.path.basename(file_path))[0]
                temp_dir = temp_dir_from_env

                console.print(f"\n[cyan]Обработка файла: {os.path.basename(file_path)}[/cyan]")
                try:
                    with console.status("[bold green]Подготовка аудио...") as status:
                        if file_path.lower().endswith(".mp3"):
                            # Копируем в temp, чтобы не мутировать оригинал
                            ensure_dir_exists(temp_dir)
                            import shutil

                            dst = os.path.join(temp_dir, os.path.basename(file_path))
                            status.update("[cyan]Копирование файла...")
                            shutil.copy(file_path, dst)
                            audio_file_path = dst
                        elif file_path.lower().endswith(".mp4"):
                            audio_file_path, _ = extract_audio_from_local_file(
                                file_path, temp_dir, status
                            )

                    if not audio_file_path:
                        console.print(
                            f"[red]Не удалось подготовить аудио из {os.path.basename(file_path)}[/red]"
                        )
                        continue

                    with console.status("[bold green]Транскрибация (API)...") as status:
                        transcribe_audio_api(
                            audio_file_path,
                            video_title,
                            output_dir=transcriptions_dir,
                            status=status,
                            model=default_model,
                            language=default_lang,
                        )
                except Exception as e:
                    console.print(
                        f"\n[bold red]Ошибка при обработке файла {os.path.basename(file_path)}:[/bold red] {e}"
                    )
                finally:
                    if audio_file_path:
                        cleanup_temp_files(audio_file_path)

            console.print("\n[bold green]Пакетная обработка завершена.[/bold green]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Процесс прерван пользователем.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[bold red]Непредвиденная ошибка:[/bold red] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

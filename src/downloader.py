import os
import yt_dlp
from rich.console import Console
from .utils import sanitize_filename, ensure_dir_exists

console = Console(stderr=True, record=True)

class YtdlpLogger:
    """Логгер для yt-dlp, чтобы перехватывать его вывод."""
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        console.print(f"[yellow]WARNING:[/] {msg}", highlight=False)

    def error(self, msg):
        console.print(f"[red]ERROR:[/] {msg}", highlight=False)

def download_audio(url, temp_dir="temp", status=None):
    """
    Скачивает аудио с YouTube, обновляя текстовый статус.
    Возвращает путь к аудиофайлу и его оригинальное название.
    """
    ensure_dir_exists(temp_dir)

    def ytdlp_progress_hook(d):
        """Hook для отслеживания прогресса скачивания в yt-dlp."""
        if status:
            if d['status'] == 'downloading':
                # Обновляем статус, показывая процент скачивания
                percent = d['_percent_str'].strip()
                status.update(f"[cyan]Скачивание аудио... {percent}")
            elif d['status'] == 'finished':
                status.update("[green]Загрузка завершена.")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'logger': YtdlpLogger(),
        'progress_hooks': [ytdlp_progress_hook],
        'nocheckcertificate': True,
        'keepvideo': False,
    }

    if status:
        status.update("[cyan]Получение информации о видео...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            
            video_title = info_dict.get('title', 'audio')
            safe_title = sanitize_filename(video_title)
            
            audio_file_path = os.path.join(temp_dir, f"{safe_title}.mp3")

            if status:
                status.update("[cyan]Скачивание аудио...")
            
            ydl.download([url])

            if not os.path.exists(audio_file_path):
                files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                if not files:
                    raise FileNotFoundError("Не удалось найти скачанный mp3 файл.")
                audio_file_path = max(files, key=os.path.getctime)

            if status:
                status.update("[green]Аудио успешно скачано.")

            return audio_file_path, video_title

        except yt_dlp.utils.DownloadError as e:
            console.print(f"\n[bold red]Ошибка скачивания:[/bold red] {e}")
            return None, None
        except Exception as e:
            console.print(f"\n[bold red]Произошла ошибка в процессе скачивания:[/bold red] {e}")
            return None, None


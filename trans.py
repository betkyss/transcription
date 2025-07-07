import yt_dlp
from pydub import AudioSegment
import os
import whisper
import torch
import time
import warnings


def download_youtube_video_as_mp3(video_url, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            title = info_dict.get('title', 'audio')
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip()
            downloaded_file = os.path.join(output_folder, f"{safe_title}.mp3")

            if not os.path.exists(downloaded_file):
                downloaded_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.mp4', '.mp3')

    except Exception as e:
        print(f"Ошибка при загрузке видео: {e}")
        return None

    print(f"Скачано MP3: {downloaded_file}")
    return downloaded_file


def compress_mp3(input_file, bitrate="64k", sample_rate=22050):
    """
    Сжимает MP3 файл до минимального размера.
    :param input_file: Путь к исходному MP3 файлу.
    :param bitrate: Целевой битрейт (например, "64k", "96k").
    :param sample_rate: Частота дискретизации в Гц (например, 22050, 44100).
    :return: Путь к сжатому MP3 файлу.
    """
    if not os.path.exists(input_file):
        print(f"Файл {input_file} не найден для сжатия.")
        return None

    compressed_file = os.path.splitext(input_file)[0] + "_compressed.mp3"

    try:
        audio = AudioSegment.from_file(input_file)
        audio.export(compressed_file, format="mp3", bitrate=bitrate, parameters=["-ar", str(sample_rate)])

        # Удаляем оригинальный файл
        os.remove(input_file)

        # Переименовываем сжатый файл в оригинальное имя
        os.rename(compressed_file, input_file)

        print(f"Сжатый файл сохранён: {input_file}")
        return input_file
    except Exception as e:
        print(f"Ошибка при сжатии файла: {e}")
        return None


def transcribe_audio(file_path, model):
    """
    Транскрибирует аудио файл с использованием Whisper.
    :param file_path: Путь к MP3 файлу.
    :param model: Загруженная модель Whisper.
    :return: Текст транскрипции.
    """
    result = model.transcribe(file_path)
    return result['text']


def download_compress_transcribe(video_urls, output_folder="downloads", bitrate="64k", sample_rate=22050):
    """
    Скачивает MP3 с YouTube, сжимает его и делает транскрипцию.
    :param video_urls: Список URL видео на YouTube.
    :param output_folder: Папка для сохранения файлов.
    :param bitrate: Целевой битрейт для сжатия.
    :param sample_rate: Частота дискретизации для сжатия.
    """
    start_time = time.time()

    # Загрузка модели Whisper
    print("Загрузка модели Whisper...")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model("small", device=device)

    processed_urls = set()  # Множество для отслеживания обработанных ссылок

    for video_url in video_urls:
        if video_url in processed_urls:
            print(f"Ссылка {video_url} уже обработана. Пропускаем...")
            continue

        print(f"\nОбработка видео: {video_url}")

        # Скачиваем MP3
        mp3_file = download_youtube_video_as_mp3(video_url, output_folder)

        if not mp3_file:
            print("Ошибка при загрузке видео. Пропускаем...")
            continue

        # Сжимаем MP3
        compressed_file = compress_mp3(mp3_file, bitrate, sample_rate)

        if not compressed_file:
            print("Ошибка на этапе сжатия. Пропускаем...")
            continue

        # Транскрибируем MP3
        print("Транскрибируем файл...")
        text = transcribe_audio(compressed_file, model)

        # Сохраняем текстовый файл
        text_filename = os.path.splitext(compressed_file)[0] + "_text.txt"
        with open(text_filename, "w") as text_file:
            text_file.write(text)

        # Удаляем сжатый MP3 файл
        os.remove(compressed_file)
        print(f"Удалён промежуточный файл: {compressed_file}")
        print(f"Транскрипция завершена. Текст сохранён в: {text_filename}")

        # Добавляем ссылку в обработанные
        processed_urls.add(video_url)

    end_time = time.time()
    total_elapsed_time = end_time - start_time
    print(f"\nОбработка завершена. Общее время выполнения: {total_elapsed_time:.2f} секунд.")


if __name__ == "__main__":
    input_data = input("Введите URL YouTube видео или путь к файлу с ссылками: ")

    if os.path.isfile(input_data):
        # Читаем ссылки из текстового файла
        with open(input_data, "r") as file:
            video_urls = [line.strip() for line in file if line.strip()]
    else:
        # Одиночный URL
        video_urls = [input_data]

    download_compress_transcribe(video_urls, output_folder="downloads", bitrate="64k", sample_rate=22050)

# Whisper YouTube Transcriber

Этот скрипт позволяет скачивать аудиодорожку с любого YouTube-видео и транскрибировать её в текст с помощью модели `whisper` от OpenAI.

## Возможности

- Скачивание аудио с YouTube по ссылке.
- Транскрибация аудио в текстовый файл.

## Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/ваш-логин/whisper-youtube-transcriber.git
    cd whisper-youtube-transcriber
    ```

2.  **Установите FFmpeg:**
    Для работы `yt-dlp` (скачивание) и `whisper` (обработка аудио) требуется `FFmpeg`.

    - **Для Arch Linux:**
      ```bash
      sudo pacman -S ffmpeg
      ```
    - **Для Debian/Ubuntu:**
      ```bash
      sudo apt update && sudo apt install ffmpeg
      ```
    - **Для macOS (используя Homebrew):**
      ```bash
      brew install ffmpeg
      ```
    - **Для Windows (используя Chocolatey):**
      ```bash
      choco install ffmpeg
      ```

3.  **Создайте виртуальное окружение и установите зависимости:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Для Linux/macOS
    # venv\Scripts\activate  # Для Windows
    pip install -r requirements.txt
    ```

## Использование

Запустите скрипт из главного каталога проекта:

```bash
python3 main.py
```

Программа запросит у вас URL YouTube-видео. Вставьте ссылку и нажмите Enter.

```
Введите URL YouTube видео: https://www.youtube.com/watch?v=...
```

После завершения процесса транскрипция будет сохранена в папке `transcriptions` в формате `.txt`.

## Структура проекта

- `main.py`: Главный файл для запуска приложения.
- `src/`: Исходный код.
  - `downloader.py`: Модуль для скачивания аудио.
  - `transcriber.py`: Модуль для транскрибац��и.
  - `utils.py`: Вспомогательные функции.
- `requirements.txt`: Список зависимостей Python.
- `.gitignore`: Файл для исключения ненужных файлов из Git.
- `temp/`: Временная папка для скачанных аудио (создается автоматически).
- `transcriptions/`: Папка для сохранения готовых транскрипций (создается автоматически).

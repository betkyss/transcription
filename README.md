# Whisper Transcriber

Этот скрипт позволяет транскрибировать аудио в текст с помощью модели `whisper` от OpenAI.

## Возможности

- Транскрибация аудио из локальных видео- и аудиофайлов (`.mp4`, `.mp3`).
- Скачивание и транскрибация аудио с YouTube по ссылке.
- Сохранение результата в текстовый файл.

## Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/betkyss/transcription.git
    cd transcription
    ```

2.  **Установите FFmpeg:**
    Для извлечения аудио из видеофайлов требуется `FFmpeg`.

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

1.  **Для локальных файлов:**
    - Поместите ваши `.mp4` или `.mp3` файлы в папку `videos`. Если папки нет, создайте её.

2.  **Запустите скрипт:**
    ```bash
    python3 main.py
    ```

3.  **Выберите опцию в меню:**
    - **Локальный файл:** Выберите файл из списка для транскрибации.
    - **URL с YouTube:** Вставьте ссылку на видео.

После завершения процесса транскрипция будет сохранена в папке `transcriptions` в формате `.txt`.

### Транскрибация через OpenAI API (без локальной модели)

1) Подготовьте `.env` (или скопируйте пример):
```bash
cp .env.example .env
# отредактируйте .env и укажите ваш OPENAI_API_KEY
```

Ключевые переменные в `.env`:
- `OPENAI_API_KEY` — обязательный ключ OpenAI
- `OPENAI_BASE_URL` — необязательно, если используете прокси/шлюз
- `OPENAI_TRANSCRIBE_MODEL` — модель (по умолчанию `whisper-1`)
- `OPENAI_TRANSCRIBE_LANG` — подсказка языка (например, `ru`)
- `VIDEOS_DIR` — папка с входными файлами (по умолчанию `videos`)
- `TRANSCRIPTIONS_DIR` — папка для текстов (по умолчанию `transcriptions`)
- `TEMP_DIR` — временная папка (по умолчанию `temp`)

2) Установите зависимости:
```bash
pip install -r requirements.txt
```

3) Запустите отдельный скрипт API-транскрибации:
```bash
python3 transcribatsc.py
```
Функционал аналогичен `main.py`: можно выбирать локальные файлы из `VIDEOS_DIR` или указывать ссылку YouTube. Результаты сохраняются в `TRANSCRIPTIONS_DIR`.

## Структура проекта

- `main.py`: Главный файл для запуска приложения.
- `transcribatsc.py`: Отдельный скрипт для транскрибации через OpenAI API.
- `src/`: Исходный код.
  - `downloader.py`: Модуль для скачивания и извлечения аудио.
  - `transcriber.py`: Модуль для транскрибации.
  - `utils.py`: Вспомогательные функции.
- `videos/`: Папка для ваших локальных медиафайлов.
- `transcriptions/`: Папка для сохранения готовых транскрипций (создается автоматически).
- `temp/`: Временная папка для аудиофайлов (создается и очищается автоматически).
- `requirements.txt`: Список зависимостей Python.
- `.gitignore`: Файл для исключения ненужных файлов из Git.

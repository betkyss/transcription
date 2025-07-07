import os
import whisper
import time

# Папка с аудиофайлами
input_folder = input("Путь: ")  # Замените на путь к вашей папке с .mp3 файлами

# Функция для обработки аудиофайла
def transcribe_audio(file_path, model):
    result = model.transcribe(file_path)
    return result['text']

# Загрузка модели на CUDA
model = whisper.load_model("small", device="cuda")

# Запуск процесса
start_time = time.time()

# Словарь для хранения времени обработки каждого файла
file_times = {}

# Процесс обработки всех файлов в папке
for filename in os.listdir(input_folder):
    if filename.endswith(".mp3"):
        mp3_path = os.path.join(input_folder, filename)

        # Замер времени для каждого файла
        file_start_time = time.time()

        # Транскрибируем аудио
        text = transcribe_audio(mp3_path, model)

        # Записываем текст в файл
        text_filename = f"{os.path.splitext(filename)[0]}_text.txt"
        text_file_path = os.path.join(input_folder, text_filename)

        with open(text_file_path, "w") as text_file:
            text_file.write(text)

        # Замер времени окончания обработки файла
        file_end_time = time.time()
        file_elapsed_time = file_end_time - file_start_time
        file_times[filename] = file_elapsed_time

        print(f"Транскрипт для {filename} сохранён в {text_filename}. Время обработки: {file_elapsed_time:.2f} секунд.")

# Завершаем процесс и выводим общее время
end_time = time.time()
total_elapsed_time = end_time - start_time

# Вывод итогов
print("\nОбработка завершена.")
for filename, file_time in file_times.items():
    print(f"{filename}: {file_time:.2f} секунд")
print(f"\nОбщее время выполнения: {total_elapsed_time:.2f} секунд.")

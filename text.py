import os

def merge_files_with_headers(input_folder, output_file):
    """
    Объединяет файлы из указанной папки в один с разделением по заголовкам исходных файлов.

    :param input_folder: Путь к папке с файлами для объединения.
    :param output_file: Путь для сохранения итогового файла.
    """
    try:
        # Получаем список всех файлов в папке
        input_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]

        with open(output_file, 'w', encoding='utf-8') as outfile:
            for file_path in input_files:
                header = f"\n--- Начало файла: {os.path.basename(file_path)} ---\n"
                outfile.write(header)

                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())

                footer = f"\n--- Конец файла: {os.path.basename(file_path)} ---\n"
                outfile.write(footer)

        print(f"Все файлы из папки {input_folder} успешно объединены в {output_file}")
    except Exception as e:
        print(f"Ошибка при объединении файлов: {e}")

# Пример использования
if __name__ == "__main__":
    # Замените этот путь на путь к вашей папке с файлами
    input_folder = input('путь к папке: ')
    output_file = "merged_file.txt"

    merge_files_with_headers(input_folder, output_file)


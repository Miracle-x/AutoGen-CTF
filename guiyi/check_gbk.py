import os

def check_gbk_encoding(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        content.decode('gbk')
        print(f"{file_path} is valid GBK encoded.")
    except UnicodeDecodeError as e:
        error_position = content[:e.start].count(b'\n') + 1
        error_column = e.start - content[:e.start].rfind(b'\n') - 1
        print(f"Encoding error in {file_path}: byte {e.start} - {e.end} at line {error_position}, column {error_column}")

def check_directory_for_gbk(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.jsonl'):
                file_path = os.path.join(root, file)
                print(f"Checking {file_path}...")
                check_gbk_encoding(file_path)

if __name__ == "__main__":
    directory = input("Enter the directory path to check for GBK encoded JSONL files: ")
    check_directory_for_gbk(directory)

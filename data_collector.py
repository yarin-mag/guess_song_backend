import os

def collect_python_files_content(start_path='.'):
    output_file = 'all.txt'
    excluded_dirs = {'.venv'}  # Add more if needed

    with open(output_file, 'w', encoding='utf-8') as out:
        for root, dirs, files in os.walk(start_path):
            # Modify dirs in-place to skip excluded directories like `.venv`
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                if 'data_collector' not in file and file.endswith('.py') and file != output_file:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, start_path)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        out.write(f"// {rel_path}\n{content}\n\n")
                    except Exception as e:
                        print(f"Could not read {file_path}: {e}")

if __name__ == "__main__":
    collect_python_files_content()

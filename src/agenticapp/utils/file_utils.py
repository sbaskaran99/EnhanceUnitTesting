import os
import tempfile
import zipfile
import shutil
def list_files(directory, extensions=None):
    if extensions is None:
        extensions = [".py"]
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(tuple(extensions))]


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8",errors="replace") as file:
        content = file.read()
        # Replace single curly braces with double curly braces
        content = content.replace('{', '{{').replace('}', '}}')
    return content

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w',encoding="utf-8", errors="replace") as f:
        f.write(content)

def create_init_files(directory):
    """Recursively create __init__.py files in all parent directories."""
    while directory and directory != os.path.dirname(directory):  # Stop at root
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass  # Create an empty __init__.py
        directory = os.path.dirname(directory)  # Move up to the parent directory        

def create_output_folder(output_folder):
    """Create the output folder if it doesn't exist."""
    os.makedirs(output_folder, exist_ok=True)

def extract_zip_file(uploaded_zip_file):
    """Extract the contents of the uploaded zip file to a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(uploaded_zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def remove_readonly(func, path, excinfo):
    """Handles read-only files by changing permissions."""
    os.chmod(path, 0o777)  # Set full permissions
    func(path)

def clear_directories(directories_to_clear):
    """Clears the contents of the specified directories."""
    for directory in directories_to_clear:
        try:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        print(f"Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, onerror=remove_readonly)
                        print(f"Deleted directory: {file_path}")
            else:
                print(f"Directory not found: {directory}")
        except Exception as e:
            print(f"Error clearing directory {directory}: {e}")

def find_test_file(source_file, test_dir):
    # Derive the base name of the source file without extension
    base_name = os.path.splitext(os.path.basename(source_file))[0]
    # Search for test files with numeric suffixes
    for i in range(10):  # Adjust the range as needed
        test_file_name = f"test_{base_name}_{i}.py"
        test_file_path = os.path.join(test_dir, test_file_name)
        if os.path.exists(test_file_path):
            #print(f"Found test file: {test_file_path}")
            return test_file_path
    print(f"No test file found for {source_file}.")
    return None 
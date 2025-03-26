import os
import tempfile
import zipfile

def list_files(directory, extensions=None):
    if extensions is None:
        extensions = [".py"]
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(tuple(extensions))]


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        # Replace single curly braces with double curly braces
        content = content.replace('{', '{{').replace('}', '}}')
    return content

def write_file(file_path, content):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
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


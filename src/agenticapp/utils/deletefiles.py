import os
import shutil

def delete_files_and_folders():
    files_to_delete = [
        "D:\\Sai\\EnhanceUnitTesting\\test_results.html",
        "D:\\Sai\\EnhanceUnitTesting\\test_results.json",
        "D:\\Sai\\EnhanceUnitTesting\\coverage_report.txt",
        "D:\\Sai\\EnhanceUnitTesting\\coverage_report1.txt",
        "D:\\Sai\\EnhanceUnitTesting\\fixed_testcaseresults.html",
        "D:\\Sai\\EnhanceUnitTesting\\fixed_testcaseresults.json",
        "D:\\Sai\\EnhanceUnitTesting\\results.html",
        "D:\\Sai\\EnhanceUnitTesting\\results.json",
        "D:\\Sai\\EnhanceUnitTesting\\improved_testcaseresults.html",
        "D:\\Sai\\EnhanceUnitTesting\\improved_testcaseresults.json",
    ]
    
    directories_to_clear = [
        "D:\\Sai\\EnhanceUnitTesting\\source_files",
        "D:\\Sai\\EnhanceUnitTesting\\tests",
        "D:\\Sai\\EnhanceUnitTesting\\coverage_html_report",
        "D:\\Sai\\EnhanceUnitTesting\\coverage_html1_report",
        "D:\\Sai\\EnhanceUnitTesting\\.cache"
    ]
    
    # Delete specified files
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted file: {file}")
            else:
                print(f"File not found: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")
    
    # Clear the contents of specified directories
    for directory in directories_to_clear:
        try:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        print(f"Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"Deleted directory: {file_path}")
            else:
                print(f"Directory not found: {directory}")
        except Exception as e:
            print(f"Error clearing directory {directory}: {e}")

if __name__ == "__main__":
    delete_files_and_folders()

import re
import os
def parse_coverage_report(file_path):
    low_coverage_files = []
    
    # Open the file with appropriate encoding (likely UTF-16)
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    for line in lines:
        line = line.replace('\x00', '').strip()  # Remove null bytes and strip whitespace
        #print(f"Processing line: {line}")  # Debugging print
        # Match lines with filename, statements, misses, and coverage percentage
        match = re.match(r"(\S+)\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", line)
        if match:
            file_name = match.group(1).strip()
            coverage = int(match.group(2))
            if coverage < 100:
                low_coverage_files.append((file_name, coverage))
        else:
            print(f"No match for line: {line}")  # Debug unmatched lines
    
    return low_coverage_files


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


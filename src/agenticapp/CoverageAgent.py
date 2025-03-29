import coverage
import pandas as pd
import re
import os
import sys
import unittest
from dotenv import load_dotenv
from autogen import AssistantAgent, config_list_from_json
from utils.file_utils import find_test_file
from TestGenerationAgent import clean_generated_code  # External function to clean AI response

# --------------------------
# Module-level setup
# --------------------------
load_dotenv()

config_path = r"D:\Sai\EnhanceUnitTesting\src\agenticapp\OAI_CONFIG_LIST.json"
config_list = config_list_from_json(config_path)

for config in config_list:
    if "api_key" in config and config["api_key"] == "ENV_OPENAI_API_KEY":
        config["api_key"] = os.getenv("OPENAI_API_KEY")

coverage_agent = AssistantAgent(
    name="CoverageAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)
test_generation_agent = AssistantAgent(
    name="TestGenerationAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

# Update sys.path so that modules under source_files can be imported.
current_dir = os.path.dirname(os.path.abspath(__file__))
source_files_root = current_dir.replace(os.path.sep + "tests", os.path.sep + "source_files")
def add_parent_directories_to_sys_path(path):
    while path not in sys.path and os.path.isdir(path):
        sys.path.insert(0, path)
        path = os.path.dirname(path)
        if path == os.path.dirname(path):
            break
add_parent_directories_to_sys_path(source_files_root)

# --------------------------
# Coverage measurement setup
# --------------------------
cov = coverage.Coverage(
    omit=["*/tests/*", "*/__init__.py"],
    include=["*/source_files/*"],
    branch=True
)
cov.start()

# --------------------------
# Helper functions for updating test file
# --------------------------
def measure_coverage(test_folder, coverage_report_file="coverage_report.txt"):
    """
    Runs tests, stops coverage, and writes a report.
    """
    print("📊 Measuring test coverage...")
    loader = unittest.defaultTestLoader
    suite = loader.discover(test_folder, pattern="test_*.py")
    if suite.countTestCases() == 0:
        print("⚠️ No test cases found.")
        return
    unittest.TextTestRunner().run(suite)
    cov.stop()
    cov.save()
    with open(coverage_report_file, "w", encoding="utf-8") as f:
        cov.report(file=f)
    cov.html_report(directory="coverage_html_report")
    print(f"✅ Coverage report saved to {coverage_report_file}")
    print("📊 HTML report generated in 'coverage_html_report/'")

def display_coverage_report(COVERAGE_REPORT_PATH):
    """Read and display coverage report in a tabular format."""
    if os.path.exists(COVERAGE_REPORT_PATH):
        with open(COVERAGE_REPORT_PATH, "r") as f:
            lines = f.readlines()

        # Extract table-like data
        data = []
        for line in lines:
            if "%" in line:  # Look for coverage percentage lines
                parts = line.split()
                if len(parts) >= 6:
                    data.append(parts)

        if data:
            #df = pd.DataFrame(data, columns=["File", "Statements", "Missed","Branch", "BrPart", "Coverage"])
            df = pd.DataFrame(data, columns=["File", "Statements", "Missed","Branches", "BrMissed", "Coverage"])
            df["Coverage"] = df["Coverage"].str.replace("%", "").astype(float)  # Convert coverage to numeric

        return df   
    

def parse_coverage_report(file_path):
    """
    Reads the text coverage report and returns a list of tuples:
    (file_path, missing_branch_count, coverage_percent)
    """
    low_coverage_files = []
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    for line in lines:
        line = line.replace("\x00", "").strip()
        if "TOTAL" in line or "Name" in line or "-----" in line:
            continue
        match = re.match(r"(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%", line)
        if match:
            file_name = match.group(1).strip()
            missing_branches = int(match.group(5))
            coverage_percent = int(match.group(6))
            if coverage_percent < 100:
                low_coverage_files.append((file_name, missing_branches, coverage_percent))
    return low_coverage_files

def reindent_generated_code(generated_code, base_indent="    "):
    """
    Reindents the generated code:
      - Finds the minimal indentation among non-empty lines.
      - Removes that minimal indent and prepends base_indent to each line.
    Returns the reindented code.
    """
    lines = generated_code.splitlines()
    min_indent = None
    for line in lines:
        if line.strip():
            leading_spaces = len(line) - len(line.lstrip())
            if min_indent is None or leading_spaces < min_indent:
                min_indent = leading_spaces
    if min_indent is None:
        min_indent = 0
    new_lines = []
    for line in lines:
        if line.strip():
            new_lines.append(base_indent + line[min_indent:])
        else:
            new_lines.append("")
    return "\n".join(new_lines) + "\n"

def insert_tests_into_existing_class(existing_lines, new_test_methods):
    """
    Inserts the new test methods into the first class in the file that is a subclass of unittest.TestCase,
    just before the main block (or at the end of the file if no main block exists).
    The new test methods should already be properly reindented.
    
    Parameters:
      existing_lines (list): Lines from the test file.
      new_test_methods (str): New test method definitions to insert.
    
    Returns:
      list: Updated list of lines with new test methods inserted into the class.
    """
    updated_lines = []
    class_found = False
    class_indent = ""
    insert_index = None

    import re
    class_pattern = re.compile(r"^(\s*)class\s+\w+\(unittest\.TestCase\):")
    for idx, line in enumerate(existing_lines):
        m = class_pattern.match(line)
        if m:
            class_found = True
            class_indent = m.group(1)
            insert_index = idx + 1  # Insert immediately after the class header.
            break

    if not class_found:
        return existing_lines

    for idx in range(insert_index, len(existing_lines)):
        line = existing_lines[idx]
        if line.lstrip().startswith("if __name__ =="):
            insert_index = idx
            break
        if line.strip() != "":
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= len(class_indent):
                insert_index = idx
                break

    if not new_test_methods.endswith("\n"):
        new_test_methods += "\n"
    return existing_lines[:insert_index] + [new_test_methods] + existing_lines[insert_index:]

def update_test_file(test_file, generated_code):
    """
    Updates an existing test file by inserting the generated test methods into the first unittest.TestCase subclass.
    Assumes that generated_code already contains valid test method definitions.
    It reindents the generated code relative to the class declaration.
    """
    with open(test_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find the class indent from the first unittest.TestCase subclass.
    class_indent = ""
    import re
    for line in lines:
        m = re.search(r"^(\s*)class\s+\w+\(unittest\.TestCase\):", line)
        if m:
            class_indent = m.group(1)
            break

    # Reindent generated code with base indent = class_indent + 4 spaces.
    new_methods = reindent_generated_code(generated_code, base_indent=class_indent + "    ")
    print("🚀 Processed test methods to insert:\n", new_methods)
    updated_lines = insert_tests_into_existing_class(lines, new_methods)
    with open(test_file, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    print(f"✅ Updated {test_file} with new test methods.")

def generate_and_update_tests(coverage_report_file, test_folder):
    """
    Identifies files with low branch coverage, generates missing test methods,
    and inserts these methods into the first unittest.TestCase subclass in the appropriate test file.
    """
    low_coverage_files = parse_coverage_report(coverage_report_file)
    if not low_coverage_files:
        print("✅ All files have 100% coverage! No additional tests needed.")
        return
    source_root = os.path.abspath("source_files")
    for file_name, missing_branches, coverage in low_coverage_files:
        print(f"📌 Low coverage detected in {file_name} ({coverage}%) with {missing_branches} missing branch(es)")
        abs_file = os.path.abspath(file_name)
        try:
            relative_path = os.path.relpath(abs_file, source_root)
        except Exception as e:
            print(f"⚠️ Could not compute relative path for {file_name}: {e}")
            relative_path = os.path.basename(file_name)
        test_subfolder = os.path.join(test_folder, os.path.dirname(relative_path))
        if not os.path.exists(test_subfolder):
            os.makedirs(test_subfolder)
        base_name = os.path.basename(file_name).replace('.py', '')
        test_file_name = f"test_{base_name}_0.py"
        test_file = os.path.join(test_subfolder, test_file_name)
        if not os.path.exists(test_file):
            print(f"⚠️ No existing test file found: {test_file}")
            # Optionally, create a new test file here.
        else:
            print(f"🔍 Found existing test file: {test_file}")
        prompt = (
            f"Generate missing test cases for {file_name}. "
            f"The coverage is {coverage}%. There are {missing_branches} missing branch(es). "
            f"Provide only valid Python test functions (starting with 'def test_') without the class header. "
            f"Do not include any markdown or instructional text."
        )
        response = test_generation_agent.generate_oai_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        raw_test_cases = response[1].strip() if isinstance(response, tuple) else response.strip()
        cleaned_test_cases = clean_generated_code(raw_test_cases).strip()
        print("🚀 Cleaned Test Cases:\n", cleaned_test_cases)
        update_test_file(test_file, cleaned_test_cases)

if __name__ == "__main__":
    test_folder = "./tests"
    coverage_report_path = "coverage_report.txt"
    measure_coverage(test_folder, coverage_report_path)
    generate_and_update_tests(coverage_report_path, test_folder)
    print("\n🔄 Re-running tests after updating coverage...")
    measure_coverage(test_folder, coverage_report_path)


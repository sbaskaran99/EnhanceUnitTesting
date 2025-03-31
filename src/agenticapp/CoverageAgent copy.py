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

config_path = r"D:\Sai\EnhanceUnitTesting\src\agenticapp\COVERAGE_CONFIG_LIST.json"
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

def parse_coverage_report(file_path):
    """
    Reads the text coverage report and returns a list of tuples:
    (file_path, missing_statements, missing_branches, coverage_percent)
    """
    low_coverage_files = []
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    for line in lines:
        line = line.replace("\x00", "").strip()
        if "TOTAL" in line or "Name" in line or "-----" in line:
            continue
        # Expected format: File  Stmts  Miss  Branch  BrPart  Cover
        match = re.match(r"(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%", line)
        if match:
            file_name = match.group(1).strip()
            total_statements = int(match.group(2))
            missing_statements = int(match.group(3))
            total_branches = int(match.group(4))
            missing_branches = int(match.group(5))
            coverage_percent = int(match.group(6))
            if coverage_percent < 100:
                low_coverage_files.append((file_name, missing_statements, missing_branches, coverage_percent))
    return low_coverage_files


import textwrap
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
    

import textwrap

def reindent_generated_code(generated_code, base_indent="    "):
    """
    Reindents the generated code by:
      - Dedenting the entire block (removing any common leading whitespace).
      - Ensuring function definitions have the correct indentation.
      - Indenting function bodies one level deeper than the function definition.
    
    Parameters:
      generated_code (str): The code block to reindent.
      base_indent (str): The indent to prepend (e.g., class indent + 4 spaces).
    
    Returns:
      str: The properly reindented code.
    """
    dedented = textwrap.dedent(generated_code)
    lines = dedented.splitlines()
    formatted_lines = []
    inside_function = False  # Tracks if we are inside a function block

    for line in lines:
        stripped = line.lstrip()

        # If line starts with `def`, it's a function definition
        if stripped.startswith("def "):
            formatted_lines.append(base_indent + stripped)
            inside_function = True  # Next lines should be further indented
        elif inside_function and stripped:  # Indent function body lines
            formatted_lines.append(base_indent * 2 + stripped)
        elif not stripped:  # Preserve blank lines
            formatted_lines.append("")
        else:
            formatted_lines.append(base_indent + stripped)  # Regular line

    return "\n".join(formatted_lines) + "\n"





def insert_tests_into_existing_class(existing_lines, new_test_methods):
    """
    Inserts the new test methods into the first class in the file that is a subclass of unittest.TestCase,
    just before the main block (or at the end of the file if no main block exists).
    
    The new test methods should already be properly reindented.
    
    Returns the updated list of lines.
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
    import re
    class_indent = ""
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
    The prompt includes the source file content, existing test file content, coverage,
    missing statements, and missing branches information.
    """
    low_coverage_files = parse_coverage_report(coverage_report_file)
    if not low_coverage_files:
        print("✅ All files have 100% coverage! No additional tests needed.")
        return
    source_root = os.path.abspath("source_files")
    for file_name, missing_statements, missing_branches, coverage in low_coverage_files:
        print(f"📌 Low coverage detected in {file_name} ({coverage}%) - Missing statements: {missing_statements}, missing branches: {missing_branches}")
        abs_file = os.path.abspath(file_name)
        try:
            relative_path = os.path.relpath(abs_file, source_root)
        except Exception as e:
            print(f"⚠️ Could not compute relative path for {file_name}: {e}")
            relative_path = os.path.basename(file_name)
        try:
            with open(abs_file, "r", encoding="utf-8") as src:
                source_content = src.read()
        except Exception as e:
            print(f"⚠️ Could not read source file {file_name}: {e}")
            source_content = ""
        test_subfolder = os.path.join(test_folder, os.path.dirname(relative_path))
        if not os.path.exists(test_subfolder):
            os.makedirs(test_subfolder)
        base_name = os.path.basename(file_name).replace('.py', '')
        test_file_name = f"test_{base_name}_0.py"
        test_file = os.path.join(test_subfolder, test_file_name)
        if not os.path.exists(test_file):
            print(f"⚠️ No existing test file found: {test_file}")
            continue
        else:
            print(f"🔍 Found existing test file: {test_file}")
        try:
            with open(test_file, "r", encoding="utf-8") as tf:
                test_file_content = tf.read()
        except Exception as e:
            print(f"⚠️ Could not read test file {test_file}: {e}")
            test_file_content = ""
        print(missing_branches)
        prompt = (
            f"Generate missing test cases for the file {file_name}.\n"
            f"Coverage is {coverage}%. Missing statements: {missing_statements}, missing branches: {missing_branches}.\n\n"
            f"--- Source Code ---\n{source_content}\n\n"
            f"--- Existing Test Cases ---\n{test_file_content}\n\n"
            f"Ensure all conditional branches, including nested conditions and edge cases, are covered.Test cases should trigger different execution paths, including combinations of conditions where applicable."
            f"Pay special attention to nested 'if' conditions and ensure all logical paths are exercised. "
            f"For example, if an 'if' statement contains 'if A and B:', test cases must include:\n"
            f" - A=True, B=True\n"
            f" - A=True, B=False\n"
            f" - A=False, B=True\n"
            f" - A=False, B=False\n"
             f"Similarly, if an 'if' statement contains 'if A or B:', include cases for:\n"
            f" - A=True, B=True\n"
            f" - A=True, B=False\n"
            f" - A=False, B=True\n"
            f" - A=False, B=False\n"
            f"Test each if conditions for  both postive and negative values"
            f"Each test method should be defined with a 'self' parameter (e.g. 'def test_example(self):'). "
            f"Provide only valid Python test functions (starting with 'def test_') without the class header. "
            f"Do not include any markdown formatting such as ``` or ```python or instructional text."
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


import os
import ast
import re
import coverage
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from utils.chunking_utils import chunk_code

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

def generate_test_cases_with_langchain(source_chunks, existing_tests, uncovered_lines, imported_methods):
    # Initialize LangChain model
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    print("uncovered lines\n",)
    print("------------------\n")
    print(uncovered_lines)
    print("------------------\n")
    """ prompt_template = PromptTemplate(
        input_variables=["source_code", "existing_tests", "uncovered_lines","imported_methods"],
        template=(
            "The following Python code has low test coverage. Your task is to analyze the code, existing tests, "
            "and the uncovered lines to generate additional unit tests in Python's `unittest` format that maximize "
            "coverage. Focus specifically on the uncovered lines.Include tests for edge cases, boundary values, and error conditions.\n\n"
            "Include tests for the following imported methods:\n"
            "{imported_methods}.\n\n"
            "Do not replicate existing test logic.\n\n"
            "Source Code:\n```python\n{source_code}\n```\n\n"
            "Existing Tests:\n```python\n{existing_tests}\n```\n\n"
            "Uncovered Lines:\n{uncovered_lines}\n\n"
            "Output only Python code containing additional unit tests. "
            "Remove all lines starting with triple backticks ``` and any markdown syntax."
            "Do not include any markdown syntax, such as ``` or language-specific markers (like `python`)"
        ),
    ) """

    prompt_template = PromptTemplate(
    input_variables=["source_code", "existing_tests", "uncovered_lines", "imported_methods"],
    template=(
        "The following Python code has low test coverage. Your task is to analyze the code, existing tests, "
        "and the uncovered lines to generate additional unit tests in Python's `unittest` format that maximize "
        "coverage. Focus specifically on the uncovered lines. For each uncovered line, generate a test that addresses "
        "the specific functionality in that line. Ensure the generated tests target only the uncovered parts of the code.\n\n"
        "Include tests for the following imported methods:\n"
        "{imported_methods}.\n\n"
        "Do not replicate existing test logic.\n\n"
        "Source Code:\n```python\n{source_code}\n```\n\n"
        "Existing Tests:\n```python\n{existing_tests}\n```\n\n"
        "Uncovered Lines:\n{uncovered_lines}\n\n"
        "Output only Python code containing additional unit tests. "
        "Remove all lines starting with triple backticks ``` and any markdown syntax."
        "Do not include any markdown syntax, such as ``` or language-specific markers (like `python`)."
        ),
    )

    # Generate test cases for each chunk
    additional_tests = []
    for chunk in source_chunks:
        prompt = prompt_template.format(
            source_code=chunk,
            existing_tests=existing_tests,
            uncovered_lines="\n".join([f"Line {line}" for line in uncovered_lines]),
            imported_methods=", ".join(imported_methods),
        )
        response = llm.invoke(prompt)
        additional_tests.append(response.content.strip())

    return "\n\n".join(additional_tests)


def find_test_file(source_file, test_dir):
    base_name = os.path.splitext(os.path.basename(source_file))[0]
    for i in range(3):  # Adjust the range as needed
        test_file_name = f"test_{base_name}_{i}.py"
        test_file_path = os.path.join(test_dir, test_file_name)
        if os.path.exists(test_file_path):
            #print(f"Found test file: {test_file_path}")
            return test_file_path
    print(f"No test file found for {source_file}.")
    return None

def normalize_class_name(class_name):
    """Normalize the class name by removing underscores and converting to lowercase."""
    return class_name.replace("_", "").lower()

def find_best_matching_class(existing_tests, normalized_class_name):
    """Find the best matching test class in the existing test code."""
    # Find all class definitions in the existing test code
    class_pattern = r'class\s+([A-Za-z0-9_]+)\('
    class_names = re.findall(class_pattern, existing_tests)
    
    # Normalize all class names in the test file
    normalized_class_names = [normalize_class_name(class_name) for class_name in class_names]
    
    # Find the closest match by comparing normalized names
    for class_name, normalized_name in zip(class_names, normalized_class_names):
        if normalized_name == normalized_class_name:
            return class_name  # Return the original class name
    
    # If no exact match is found, return None
    return None

def rename_generated_class(new_tests, matched_class_name):
    """Renames the generated test class to match the existing test class."""
    new_tests = re.sub(
        r'class\s+Test[A-Za-z0-9_]+\(',
        f'class {matched_class_name}(',
        new_tests,
        count=1,
    )
    return new_tests

def get_imported_methods(source_code):
    """Extract all methods imported from other files."""
    tree = ast.parse(source_code)
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imported_methods = []

    for imp in imports:
        if imp.module:
            for name in imp.names:
                imported_methods.append(name.name)
    return imported_methods

def append_methods_to_test_class(existing_tests, new_methods, class_name):
    """
    Appends new test methods to the specified test class in the existing test code.
    """
    # Find the best matching class from the existing tests
    normalized_class_name = normalize_class_name(class_name)
    matched_class_name = find_best_matching_class(existing_tests, normalized_class_name)
    if not matched_class_name:
        raise ValueError(f"Test class '{class_name}' not found in the existing test code.")

    class_header = f"class {matched_class_name}("
    class_start = existing_tests.find(class_header)
    if class_start == -1:
        raise ValueError(f"Test class '{matched_class_name}' not found in the existing test code.")

    # Find the position after the class header
    class_body_start = existing_tests.find("):", class_start)
    if class_body_start == -1:
        raise ValueError(f"Malformed class definition for '{matched_class_name}'.")

    # Find the end of the class body
    class_body_end = existing_tests.find("\n\n", class_body_start)
    if class_body_end == -1:
        class_body_end = len(existing_tests)    

    # Extract the class body
    class_body = existing_tests[class_body_start + 2:class_body_end]

    # Determine the indentation level
    lines = class_body.splitlines()
    if not lines:
        raise ValueError(f"Empty class body for '{class_name}'.")
    first_line = lines[0]
    indentation = len(first_line) - len(first_line.lstrip())

    # Append new methods with correct indentation
    indented_methods = "\n\n".join(
        " " * indentation + method.replace("\n", "\n" + " " * indentation)
        for method in new_methods
    )
    updated_class_body = class_body + "\n\n" + indented_methods

    # Replace the old class body with the updated one
    updated_tests = (
        existing_tests[:class_body_start + 2]
        + updated_class_body
        + existing_tests[class_body_end:]
    )
    return updated_tests

def clean_test_code(test_code):
    test_code = re.sub(r'"""(.*?)"""', '', test_code, flags=re.DOTALL)
    test_code = re.sub(r"'''(.*?)'''", '', test_code, flags=re.DOTALL)
    test_code = re.sub(r'#.*', '', test_code)
    return test_code

def extract_test_methods(test_code):
    """
    Extracts test methods from the provided test code, excluding class definitions and comments.
    """
    try:
        # Clean the code before parsing
        test_code = re.findall(r'```python(.*?)```', test_code, re.DOTALL)
        clean_code = clean_test_code("\n".join(test_code))
        # Parse the cleaned Python code
        tree = ast.parse(clean_code)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in test code: {e}")

    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            method_code = ast.unparse(node)
            methods.append(method_code)
    return methods

def get_uncovered_lines(source_file):
    """Extract uncovered lines from the coverage report."""
    cov = coverage.Coverage()
    cov.load()
    analysis = cov.analysis(source_file)
    _, _, not_covered, _ = analysis

    # Perform analysis to get uncovered line numbers
    analysis = cov.analysis(source_file)
    _, _, not_covered, _ = analysis
    
    uncovered_lines = []
    
    # Read the source file and extract the code for uncovered lines
    with open(source_file, 'r') as file:
        source_lines = file.readlines()
        for line_num in not_covered:
            uncovered_lines.append(source_lines[line_num - 1].strip())
    
    return uncovered_lines
    #return not_covered


""" def add_import_statements(existing_tests, new_imports):
 
    existing_imports = set(re.findall(r'(?:import|from)\s+[a-zA-Z0-9_\.]+', existing_tests))
    new_imports_to_add = [imp for imp in new_imports if imp not in existing_imports]
    
    imports_section_end = existing_tests.find("\n\n")
    if imports_section_end == -1:
        imports_section_end = 0  # Add imports at the start if no imports exist
    
    updated_tests = (
        existing_tests[:imports_section_end]
        + "\n".join(new_imports_to_add) + "\n\n"
        + existing_tests[imports_section_end:]
    )
    return updated_tests  """
def add_import_statements(existing_tests, new_imports):
    """
    Adds missing import statements to the test file without duplication or errors.
    """
    # Extract existing import statements from the test file
    existing_imports = set(re.findall(r'^(?:import|from)\s+[a-zA-Z0-9_\.]+', existing_tests, re.MULTILINE))
    
    # Ensure `import unittest` is properly added if missing
    if "import unittest" not in existing_imports:
        new_imports.insert(0, "import unittest")
    
    # Filter out invalid or malformed imports
    valid_new_imports = [imp for imp in new_imports if re.match(r'^(?:import|from)\s+[a-zA-Z0-9_\.]+$', imp)]

    # Find the end of the imports section
    imports_section_end = existing_tests.find("\n\n")
    if imports_section_end == -1:
        imports_section_end = 0  # Add imports at the start if no imports exist

    # Add only valid and new import statements
    new_imports_to_add = [imp for imp in valid_new_imports if imp not in existing_imports]
    updated_tests = (
        existing_tests[:imports_section_end]
        + "\n".join(new_imports_to_add) + ("\n\n" if new_imports_to_add else "")
        + existing_tests[imports_section_end:]
    )
    return updated_tests



def analyze_and_update_imports(source_code, existing_tests):
    """
    Identifies missing imports and updates the test file accordingly.
    """
    # Extract imports from the source code
    source_imports = re.findall(r'(?:import|from)\s+[a-zA-Z0-9_\.]+', source_code, re.MULTILINE)
    # Extract imports from the existing test file
    existing_imports = re.findall(r'(?:import|from)\s+[a-zA-Z0-9_\.]+', existing_tests, re.MULTILINE)

    new_imports = [imp for imp in source_imports if imp not in existing_imports]
    updated_tests = add_import_statements(existing_tests, new_imports)
    return updated_tests


def validate_test_generation(source_code, test_code):
    """
    Validates the generated test code by checking if all uncovered lines
    have corresponding test cases.
    """
    uncovered_lines = get_uncovered_lines(source_code)
    for line in uncovered_lines:
        if f"Line {line}" not in test_code:
            print(f"Warning: Line {line} does not appear to be covered by the generated tests.")



def remove_duplicate_main_blocks(test_code):
    """
    Removes duplicate `unittest.main()` blocks from the test code.

    Args:
        test_code (str): The content of the test file.

    Returns:
        str: The updated test code with only one `unittest.main()` block.
    """
    main_block_start = test_code.rfind('if __name__ == "__main__":')
    if main_block_start != -1:
        # Extract the last `unittest.main()` block
        main_block = test_code[main_block_start:].strip()
        # Remove all other `unittest.main()` occurrences
        # Remove all occurrences of `if __name__ == '__main__':` including the last one
        test_code_without_main = test_code[:main_block_start].replace(
            'if __name__ == "__main__":\n    unittest.main()', ""
        ).strip()
        # Add the single main block back at the end
        test_code =test_code_without_main+ "\n\n" + main_block
    return test_code

def update_test_file(source_file, test_file, uncovered_lines):
    """
    Updates the test file with new test cases to cover uncovered lines in the source file.

    Args:
        source_file (str): The path to the source Python file.
        test_file (str): The path to the corresponding test file.
        uncovered_lines (list): A list of uncovered lines in the source file.
    """
    # Read the source code and existing test cases
    with open(source_file, 'r') as sf:
        source_code = sf.read()
    with open(test_file, 'r') as tf:
        existing_tests = tf.read()

    # Chunk the source code for better processing with LangChain
    chunk_size = 512
    source_chunks = chunk_code(source_code, chunk_size)

    # Extract imported methods from the source file
    imported_methods = get_imported_methods(source_code)

    # Generate new test cases using LangChain
    new_tests = generate_test_cases_with_langchain(
        source_chunks,
        existing_tests,
        uncovered_lines,
        imported_methods
    )

    # Extract test methods from the generated test cases
    new_methods = extract_test_methods(new_tests)

    # Analyze existing test classes
    class_name = f"Test{os.path.splitext(os.path.basename(source_file))[0].capitalize()}"
    normalized_class_name = normalize_class_name(class_name)
    matched_class_name = find_best_matching_class(existing_tests, normalized_class_name)

    # Append methods to an existing class or add a new class
    if matched_class_name:
        updated_tests = append_methods_to_test_class(
            existing_tests,
            new_methods,
            matched_class_name
        )
    else:
        # Add a new test class at the end of the file
        updated_tests = existing_tests.strip() + "\n\n" + new_tests.strip()

    # Ensure no duplicate imports
    updated_tests = analyze_and_update_imports(source_code, updated_tests)
    # Ensure only one `unittest.main()` block
    if '__name__ == "__main__"' in updated_tests:
        updated_tests = remove_duplicate_main_blocks(updated_tests)
    else:
        # Add a single `unittest.main()` block if not present
        updated_tests += "\n\nif __name__ == '__main__':\n    unittest.main()" 
    
    
    # Write the updated test cases back to the test file
    with open(test_file, 'w') as tf:
        tf.write(updated_tests.strip() + "\n")

    print(f"Updated {test_file} with new test cases.")


def generate_and_update_tests(low_coverage_files, test_dir):
    for source_file, coverage in low_coverage_files:
        test_file = find_test_file(source_file, test_dir)
        if not test_file:
            print(f"No test file found for {source_file}. Skipping.")
            continue

        uncovered_lines = get_uncovered_lines(source_file)
        update_test_file(source_file, test_file, uncovered_lines)
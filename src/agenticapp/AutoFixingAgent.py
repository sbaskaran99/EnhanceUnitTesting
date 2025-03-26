import json
import os
import re
from autogen import AssistantAgent,config_list_from_json
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
# Load AI agent configurations
config_path = r"D:\Sai\EnhanceUnitTesting\src\agenticapp\OAI_CONFIG_LIST.json"
config_list = config_list_from_json(config_path)
# Replace the placeholder with the actual API key from .env
for config in config_list:
    if "api_key" in config and config["api_key"] == "ENV_OPENAI_API_KEY":
        config["api_key"] = os.getenv("OPENAI_API_KEY")



# Initialize OpenAI Agent
llm_config = {
    "model": "gpt-4",  # Ensure this is a valid field
    "temperature": 0.7,  # Example of another valid key
}

openai_agent = AssistantAgent(name="AutoFixingAgent",llm_config=llm_config)

# Paths for test and source code files
TEST_FOLDER = "tests"
TEST_RESULTS_FILE = "results.json"



# Load test results
def load_test_results():
    with open(TEST_RESULTS_FILE, "r") as file:
        return json.load(file)["results"]

# Identify failed tests
def extract_failed_tests(test_results):
    return [{"name": test["test"], "reason": test.get("reason", "Unknown error")} for test in test_results if test["status"] in ["FAIL", "ERROR"]]
import re

def locate_test_file(test_name):
    """ Extracts the correct test file path and searches recursively. """
    test_parts = test_name.split(".")[:-1]  # Remove function name
    class_name = test_parts[-1]  # Extract class name (e.g., TestOrderRepository)

    # Convert CamelCase class name to snake_case file name
    file_base_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()

    # Ensure correct prefix (avoid double "test_" issues)
    expected_file_prefix = file_base_name if file_base_name.startswith("test_") else f"test_{file_base_name}"
    
    test_subfolder = os.path.join(*test_parts[:-1])  # Extract expected folder structure

    print(f"[DEBUG] Searching for a test file matching: {expected_file_prefix} in {TEST_FOLDER}")

    for root, _, files in os.walk(TEST_FOLDER):
        for file in files:
            full_path = os.path.join(root, file)
            normalized_full_path = full_path.replace("\\", "/")  # Normalize path
            normalized_subfolder = test_subfolder.replace("\\", "/")

            # Match file name using prefix check (handles test_order_repository_0.py cases)
            if file.startswith(expected_file_prefix) and file.endswith(".py") and normalized_subfolder in normalized_full_path:
                print(f"[FOUND] Test file located: {full_path}")
                return full_path

    print(f"[ERROR] Test file for {test_name} not found.")
    return None

import re

def extract_test_function(test_path, test_name):
    """ Extracts the full test function from the test file. """
    with open(test_path, "r", encoding="utf-8") as file:
        content = file.read()

    test_function_name = test_name.split(".")[-1]  # Extract the function name

    # Improved regex pattern to match full function block
    test_function_pattern = rf"(?:@[\w]+\s+)?def {test_function_name}\(.*?\):\s*(?:\"\"\".*?\"\"\"\s*)?(.*?)(?=\n\ndef |\n*$)"

    match = re.search(test_function_pattern, content, re.DOTALL)

    if match:
        print(f"[SUCCESS] Extracted function: {test_function_name} from {test_path}")
        return match.group(), content
    else:
        print(f"[ERROR] Test function {test_name} not found in {test_path}")
        return None, content


def fix_test_case(test_function_code, error_reason):
    prompt = f"""
    The following test case is failing:

    ```python
    {test_function_code}
    ```

    Error:
    ```
    {error_reason}
    ```

    Please provide a corrected version of the test function.
    """

    messages = [{"role": "system", "content": "You are a helpful AI that fixes failing Python test cases."},
                {"role": "user", "content": prompt}]

    response = openai_agent.generate_reply(messages)
    
    if not response or "content" not in response:
        print("[ERROR] No response from OpenAI for:", test_function_code)
        return None

    fixed_code = response["content"].strip()

    if fixed_code == test_function_code:
        print("[WARNING] OpenAI did not modify the test case:", test_function_code)
        return None

    print("[SUCCESS] Fixed test case generated.")
    return fixed_code


# Apply regex-based fixes for common errors
def apply_regex_fix(test_name, test_function_code, error_reason):
    if "AssertionError" in error_reason:
        # Fix string formatting issues (e.g., "{1}" -> "1")
        if "!=" in error_reason:
            test_function_code = re.sub(r"{(\d+)}", r"\1", test_function_code)
            print(f"Auto-fixed string format issue in {test_name}")
        return test_function_code

    if "AttributeError" in error_reason:
        # Fix attribute mismatches (e.g., name → item)
        test_function_code = re.sub(r"\.name", ".item", test_function_code)
        print(f"Auto-fixed attribute mismatch in {test_name}")
        return test_function_code

    return None
def update_test_file(test_path, test_name, error_reason):
    test_function_code, content = extract_test_function(test_path, test_name)

    if not test_function_code:
        print(f"[ERROR] Could not extract function {test_name} from {test_path}")
        return

    # First, try regex-based fix
    fixed_code = apply_regex_fix(test_name, test_function_code, error_reason)

    # If regex fix didn't work, use GPT-4
    if not fixed_code:
        print(f"[INFO] Using OpenAI to fix {test_name}")
        fixed_code = fix_test_case(test_function_code, error_reason)

    if not fixed_code:
        print(f"[ERROR] Failed to generate a fix for {test_name}")
        return

    # Ensure function is properly replaced
    new_content = content.replace(test_function_code, fixed_code)

    # Verify that changes were made
    if new_content == content:
        print(f"[ERROR] Replacement failed for {test_name}, possible regex issue.")
        return

    # Save the updated test file
    with open(test_path, "w", encoding="utf-8") as file:
        file.write(new_content)

    print(f"[SUCCESS] Updated test case: {test_name} in {test_path}")

# Main function
def fix_failing_tests():
    test_results = load_test_results()
    failed_tests = extract_failed_tests(test_results)

    if not failed_tests:
        print("No failing tests found.")
        return

    for test in failed_tests:
        test_path = locate_test_file(test["name"])
        if test_path:
            update_test_file(test_path, test["name"], test["reason"])

if __name__ == "__main__":
    fix_failing_tests()

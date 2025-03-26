# Function to generate prompt for creating unit tests
# Define language test frameworks
LANGUAGE_TEST_FRAMEWORKS = {
    "python": "unittest",
    "java": "JUnit",
    "javascript": "Mocha",
    "csharp": "xUnit",
    "ruby": "RSpec"
}


def get_prompt(code_chunk, language="python", prompt_type="functionality", shot_type="zero_shot"):
    """Generate a prompt for the specified code chunk and language."""
    few_shot_examples = {
        "python": """
        import unittest
        from example import Calculator

        class TestCalculator(unittest.TestCase):
            def test_add(self):
                calc = Calculator()
                self.assertEqual(calc.add(2, 3), 5)

        if __name__ == "__main__":
            unittest.main()
        """,
        "java": """
        import org.junit.Test;
        import static org.junit.Assert.*;

        public class CalculatorTest {
            @Test
            public void testAdd() {
                Calculator calc = new Calculator();
                assertEquals(5, calc.add(2, 3));
            }
        }
        """
    }

    test_framework = LANGUAGE_TEST_FRAMEWORKS.get(language, "unittest")
    examples = few_shot_examples.get(language, "")
     
   
    return f"""
    Create comprehensive edge-case unit test code for the following {language} class or functions:
    {code_chunk}

    
    Requirements:
            1.  Assume the class or functions are defined in a module located in the 'source_files' directory, 
                which is a sibling directory of the test script. Dynamically add the 'source_files' directory 
                to sys.path to ensure imports work correctly. For example:
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # Remove 'tests' from the current directory path to find the root of the source files

                source_files_root = current_dir.replace("\\tests", "\\source_files").replace("/tests", "/source_files")
                # Function to recursively add parent directories to sys.path
                def add_parent_directories_to_sys_path(path):
                     while path not in sys.path and os.path.isdir(path):
                        sys.path.insert(0, path)
                        path = os.path.dirname(path)  # Move up one directory
                        if path == os.path.dirname(path):  # Stop at root
                        break

                # Add the 'source_files_root' and its parents
                add_parent_directories_to_sys_path(source_files_root)
                              
                # Append the relative path from the current test directory, excluding duplicates
                #relative_test_path = os.path.relpath(current_dir, os.path.abspath(os.path.join(current_dir, "..", "tests")))
                #source_files_path = os.path.normpath(os.path.join(source_files_root, relative_test_path))
                # Add the source_files directory to sys.path
                if source_files_path not in sys.path:
                    sys.path.insert(0, source_files_path)
             
            2.Import the relevant class or functions from the specified module. For example, if the file name is 
                'example.py' and the class name is 'Calculator', import it as:
                from example import Calculator
                If the file contains an **abstract class**, ensure the following are included:
                  from abc import ABC, abstractmethod
                  from typing import List, Optional
            3. **Handling Abstract Classes and Methods**
                 - If the given class is an **abstract class (ABC)**:
                 - Identify all abstract methods.
                - Use a **mock subclass** to implement abstract methods during testing.
                 - Example:
                     class MockExample(AbstractExample):
                     def required_method(self):
                         return "Mocked Result"
            4.  Ensure that the module name corresponds to the actual location of the class and is dynamically replaced based on the file name 
            5. **Escape Special Characters**: If the code contains double quotes ("), backslashes, or any other special characters, make sure they are properly escaped.
            
            6. **Mock External Dependencies**: For any external dependencies such as 'settings', 're' (regular expressions), or other imported modules, mock them with appropriate mock values in the test.
               **Core Functionality**: Focus on testing the core logic of the functions or methods without invoking external dependencies. For example:
                - If the method uses 'settings.PASSWORD_MIN_LENGTH', mock the 'PASSWORD_MIN_LENGTH' value.
                - If the method uses regular expressions (e.g., re.compile), mock the regex values used for validation.
            7.  ** When patching, ensure the path used in '@patch' matches the module's import style. For example: If the method 'randint' is imported as 'from random import randint', you must patch it as 'random.randint'
            8. ** Context is Clear: Analyze the purpose of each class/function and explain what is being tested in each case.
            9   ** Validate the test output against the function logic.Debug if necessary, explaining why the output may be incorrect and correct output if required
            10  **  Include edge cases such as:
                - Handling invalid inputs (e.g., incorrect data types, out-of-range values).
                - Testing boundary values (e.g., maximum and minimum allowable inputs).
                - Unexpected scenarios (e.g., empty inputs, null values).
                - **Ensure that ID values are positive integers and do not allow zero or negative IDs.**
                -Ensure that division correctly handles negative and positive numbers.
                -Allow division where the numerator is zero (0 / x should return 0).
                - **Test cases must validate that invalid IDs like zero or negative IDs raise the expected 'ValueError'.**
                - **Test cases must validate that invalid IDs raise the expected 'ValueError'.**
            11. Include meaningful error-handling tests. Verify that appropriate exceptions are raised 
                for invalid inputs or unexpected scenarios. 
                 - Validate that appropriate exceptions are raised for invalid inputs
                 - **Mock functions that should raise 'ValueError' when given invalid input.**  
                 - Example: 
                    from unittest.mock import MagicMock
                    repository.find_by_id = MagicMock(side_effect=ValueError("ID must be a positive integer"))
                    with self.assertRaises(ValueError):
                        repository.find_by_id(-1)
                - **Mock 'save()' to raise 'TypeError' for invalid input ('None')**
                - repository.save = MagicMock(side_effect=TypeError("Expected an instance of Order"))
                - with self.assertRaises(TypeError):
                        repository.save(None)  
            12. Generate individual test cases for ior each test data point separately:               
            12. Add clear and descriptive comments for each test case to explain what is being tested and why.
            13.Include a setUp() method to reset any class-level counters or states before each test. 
            14.Ensure the generated code:
                - Is properly formatted.
                - Adheres to {language} coding standards.
                - Is compatible with common unit test frameworks (e.g., unittest for Python).
            15. Add a 'main' method at the end of the test script to allow standalone execution if not present. 
                For example, in Python:
                if __name__ == "__main__":
                    unittest.main()
            16.Output a complete, ready-to-execute unit test script that compiles successfully 
            and ensures the tests cover edge cases comprehensively.
            17.Remove all  lines starting with triple backticks ```
            18.Do not include any markdown syntax, such as ``` or language-specific markers (like `python`)
            Handle Special Characters: For special characters, the prompt instructs the test generation process to ensure that any double quotes or backslashes are escaped properly, and string literals are handled correctly.
            19. filter out class variables and static method references from the input variables
            Mock Dependencies: The test generation script will replace real dependencies (like settings, re, etc.) with mocked or hardcoded values. For example:
            Mock settings.PASSWORD_MIN_LENGTH = 8
            Mock regex patterns for special characters, numeric values, etc.
            20 Automate for Multiple Files: The prompt can be fed into a script that processes multiple files. The script will:
            Extract methods/functions from each file.Use the template to generate unit test cases for each method.
            21.Ensure that special characters and external dependencies are handled properly across all files.
            22.Ensure code compiles and correct any import errors
            Example:
    {examples}
    """


# Function to generate prompt for creating unit tests
# Define language test frameworks
LANGUAGE_TEST_FRAMEWORKS = {
    "python": "unittest",
    "java": "JUnit",
    "javascript": "Mocha",
    "csharp": "xUnit",
    "ruby": "RSpec"
}

def get_prompt(code_chunk, file_name, language="python", prompt_type="functionality", shot_type="zero_shot"):
    module_name = file_name.replace(".py", "")  # Extract module name from file name
    
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
    Create a comprehensive, edge-case-focused unit test suite for the following {language} class or functions:
    {code_chunk}

    **Requirements:**
    
    1. Import 'unittest' module and necessary dependencies for all test classes
        -import unittest 
    2. **Ensure `sys.path` is updated before importing modules**  
       - Dynamically determine the 'source_files' directory before importing other modules.
       - Update `sys.path` before attempting imports.
       - Example:
         ```python
         import sys
         import os

         current_dir = os.path.dirname(os.path.abspath(__file__))
         source_files_root = current_dir.replace(os.path.sep + "tests", os.path.sep + "source_files")

         def add_parent_directories_to_sys_path(path):
             while path not in sys.path and os.path.isdir(path):
                 sys.path.insert(0, path)
                 path = os.path.dirname(path)  # Move up one level
                 if path == os.path.dirname(path):  # Stop at root
                     break

         add_parent_directories_to_sys_path(source_files_root)
         ```

    
    3.**Import the module dynamically based on the file name**  
       ```python
       from {module_name} import *
       ```
    
    4. **Implement a test class using `{test_framework}`**  
       -import unittest  first before inheriting test class from 'unittest.TestCase'
       - The test class should inherit from `unittest.TestCase` for Python.
       -import unittest 
       - Include a `setUp()` method to reset any class-level counters before each test.

    5. **Ensure test coverage for all possible edge cases, including:**
       - Valid inputs.
       - Invalid inputs (e.g., wrong data types, out-of-range values).
       - Boundary values (e.g., min/max inputs).
       - Unexpected scenarios (e.g., empty inputs, null values).
       - Ensuring invalid IDs (e.g., zero or negative IDs) raise `ValueError`.

    6. **Handle Abstract Classes Properly**  
       - If the file contains an abstract class:
         ```python
         from abc import ABC, abstractmethod
         from typing import List, Optional
         ```
       - Use a mock subclass to implement abstract methods during testing.
       - Example:
         ```python
         class MockExample(AbstractExample):
             def required_method(self):
                 return "Mocked Result"
         ```

    7. **Mock External Dependencies**  
       - Patch external dependencies such as `settings` and `re`:
         ```python
         from unittest.mock import MagicMock
         settings.PASSWORD_MIN_LENGTH = 8
         ```

    8. **Ensure proper patching in unit tests**
       - If a method is imported as `from random import randint`, patch it as `random.randint`.

    9. **Provide Clear Documentation and Comments**  
       - Each test case should have a docstring or comment explaining its purpose.
       - Example:
         ```python
         def test_invalid_id_negative(self):
             \"\"\"Test that a negative ID raises ValueError.\"\"\"
             with self.assertRaises(ValueError):
                 Order("Peach", 2, id=-5)
         ```

    10. **Verify Exceptions and Edge Cases Properly**  
       - Ensure that exceptions are explicitly tested.
       - Example:
         ```python
         repository.find_by_id = MagicMock(side_effect=ValueError("ID must be a positive integer"))
         with self.assertRaises(ValueError):
             repository.find_by_id(-1)
         ```

    11. **Ensure Each Edge Case Has a Separate Test Case**  
        - Avoid combining multiple edge cases into a single test method.

    12.**Verify String Representation Matches the Actual Implementation**  
    - Ensure that expected string formatting correctly reflects the class implementation.  
    - Construct the expected string explicitly using the class attributes, not just `str(instance)`.  
    - Example for a `__str__` method in any class:
      ```python
      instance = MyClass(arg1, arg2)  # Replace with actual constructor params
      expected_str = f"MyClass(arg1={{instance.arg1}}, arg2={{instance.arg2}})"  # Ensure correct format
      self.assertEqual(str(instance), expected_str)
      ```  

    13. **Follow Coding Standards and Formatting**  
        - Use appropriate test framework conventions.
        - Ensure the generated code is PEP 8 compliant (for Python).

    14. **Include a Main Execution Block for Running Tests**  
        - Add the following block to ensure standalone execution:
        ```python
        if __name__ == "__main__":
            unittest.main()
        ```

    15. **Ensure the Output is a Fully Functional, Executable Test Script**  
        - Do not include any markdown syntax, such as ``` or language-specific markers (like `python`)
        -Remove all  lines starting with triple backticks ```
        -The final output should be an executable test file that can be run without modifications.

    **Example Test File:**
    {examples}
    """


import os
import logging
import re
import subprocess
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from utils.chunking_utils import chunk_code
from utils.file_utils import list_files, read_file, write_file,create_init_files
from dotenv import load_dotenv
from template_prompts import get_prompt
# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",  # Logs will be saved to `app.log` file
    filemode="w"         # Optional: overwrites the log file each time the script runs
)

logger = logging.getLogger(__name__)

# List of standard modules to skip updating
STANDARD_MODULES = {
    "os", "sys", "re", "typing", "json", "collections", "itertools",
    "functools", "math", "datetime", "time", "subprocess", "logging", "List", "Optional"
}

# Get the OpenAI API key from the environment
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define language test frameworks
LANGUAGE_TEST_FRAMEWORKS = {
    "python": "unittest",
    "java": "JUnit",
    "javascript": "Mocha",
    "csharp": "xUnit",
    "ruby": "RSpec"
}

# Function to generate tests using LLMChain
def generate_tests_with_llm_chain(code_chunk, language="python", shot_type="few_shot"):
    """Generate unit tests for a code chunk using an LLMChain."""
    try:
        client = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        #prompt_template = PromptTemplate.from_template(get_prompt(code_chunk, language, "functionality", shot_type))
        
        prompt_template = PromptTemplate(template=get_prompt(code_chunk, language, "functionality", shot_type))
        prompt_template.input_variables = []
              
        # Chain using `RunnableSequence` syntax
        functionality_chain = prompt_template | client
        
        functionality_tests_response = functionality_chain.invoke({"input": code_chunk})
        functionality_tests = functionality_tests_response.content.strip()

       
        return functionality_tests

    except Exception as e:
        logger.error(f"Error generating tests: {e}")
        raise
# Function to read and update the generated unit test file
def update_test_file(output_file):
    """Read the generated test file and update module imports."""
    try:
        # Read the test file content
        content = read_file(output_file)

        # Derive the module name from the output file name
        base_name = os.path.basename(output_file)  # e.g., "test_urls_0.py"
        module_name = os.path.splitext(base_name)[0]  # Remove file extension
        module_name = re.sub(r'^test_', '', module_name)  # Remove "test_" prefix
        module_name = re.sub(r'_\d+$', '', module_name)  # Remove trailing digits (e.g., "_0")
        logger.info(f"Module name is  {module_name}")
        # Update imports only if the module is not in the standard modules list
        def replace_imports(match):
            imported_module = match.group(1)
            if imported_module not in STANDARD_MODULES:
                return f'from {module_name} import'
            return match.group(0)  # Keep the original import if it's a standard module
        
        updated_content = re.sub(
            r'\bfrom\s+(\w+)\s+import\b',  # Matches "from <module> import"
            replace_imports,
            content
        ) 
       
        # Remove any existing assignment to source_files_root
        updated_content = re.sub(
            r'source_files_root\s*=\s*.*',  # Matches existing `source_files_root` assignments
            '',
            updated_content
        )
         # Add the new assignment to `source_files_root` after `current_dir` assignment
        new_assignment = 'source_files_root = current_dir.replace("\\\\tests", "\\\\source_files").replace("/tests", "/source_files")\n'

        # Split content by lines and insert the new assignment after current_dir assignment
        lines = updated_content.splitlines()
        for i, line in enumerate(lines):
            if re.match(r'current_dir\s*=', line):  # Look for current_dir assignment
                lines.insert(i + 1, new_assignment)  # Insert the new assignment after this line
                break  # Stop after inserting

        # Join the lines back into the final content
        final_content = '\n'.join(lines)        
        # Write back the updated content to the test file
        write_file(output_file, final_content)
        logger.info(f"Updated module imports in {output_file}")

    except Exception as e:
        logger.error(f"Error updating test file {output_file}: {e}")
        raise
# Function to process a file and generate unit tests
def process_file(file_path, output_folder="tests", language="python", shot_type="few_shot"):
    """Process a file and generate unit tests for its code chunks."""
    try:
        code = read_file(file_path)
        chunk_size = 512
        code_chunks = chunk_code(code, max_chunk_size=chunk_size)
        source_folder=  "source_files"  
        # Create a mirrored subfolder structure in the output folder
        relative_path = os.path.relpath(file_path, source_folder)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        test_subfolder = os.path.join(output_folder, os.path.dirname(relative_path))
        os.makedirs(test_subfolder, exist_ok=True)
        #Ensure each subfolder in the path has an __init__.py file
        create_init_files(test_subfolder)
        for i, chunk in enumerate(code_chunks):
            output_file = os.path.join(test_subfolder, f"test_{base_name}_{i}.py")
            test_code = generate_tests_with_llm_chain(chunk, language=language, shot_type=shot_type)
            write_file(output_file, test_code)
            logger.info(f"Generated tests for chunk {i} in {output_file}")
            #Update the test file for module imports
            update_test_file(output_file)

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise    
import os
import logging
import re
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from utils.chunking_utils import chunk_code
from utils.file_utils import list_files, read_file, write_file
from dotenv import load_dotenv
from template_prompts import get_prompt
from langchain_groq import ChatGroq
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

# Get the OpenAI API key from the environment
#openai_api_key = os.getenv("OPENAI_API_KEY")4
api_key = os.environ.get("GROQ_API_KEY")

# Define language test frameworks
LANGUAGE_TEST_FRAMEWORKS = {
    "python": "unittest",
    "java": "JUnit",
    "javascript": "Mocha",
    "csharp": "xUnit",
    "ruby": "RSpec"
}



# Function to generate tests using LLMChain
def generate_tests_with_llm_chain(code_chunk, language="python", shot_type="zero_shot"):
    """Generate unit tests for a code chunk using an LLMChain."""
    try:
        #client = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        client=ChatGroq(model="mixtral-8x7b-32768",api_key=api_key)
        #client=ChatGroq(model="llama-3.3-70b-versatile",api_key=api_key)
        #client=ChatGroq(model="gemma2-9b-it",api_key=api_key)
        #client = ChatOpenAI( model="gpt-4o-mini",  temperature=0.7, openai_api_key=os.environ.get("GROQ_API_KEY"),
        #openai_api_base="https://api.groq.com/openai/v1")
        #prompt_template = PromptTemplate.from_template(get_prompt(code_chunk, language, "functionality", shot_type))
        
        prompt_template = PromptTemplate(template=get_prompt(code_chunk, language, "functionality", shot_type))
        prompt_template.input_variables = []
              
        # Chain using `RunnableSequence` syntax
        functionality_chain = prompt_template | client
        
        functionality_tests_response = functionality_chain.invoke({"input": code_chunk})
        functionality_tests = functionality_tests_response.content.strip()

        # Add the main method if missing
        """ if "__name__ == '__main__'" not in functionality_tests:
            functionality_tests += "\n\nif __name__ == '__main__':\n    unittest.main()"
        """
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
        # Replace "your_module_name" with the derived module name
        #updated_content = re.sub(r'\byour_module_name\b', module_name, content)
        # Matches statements like: "from example import delete_nth, delete_nth_naive"
        updated_content = re.sub(
            r'\bfrom\s+\w+\s+import\b',  # Matches "from <module> import"
            f'from {module_name} import',
            content
        ) 
        # Write back the updated content to the test file
        write_file(output_file, updated_content)
        logger.info(f"Updated module imports in {output_file}")

    except Exception as e:
        logger.error(f"Error updating test file {output_file}: {e}")
        raise
# Function to process a file and generate unit tests
def process_file(file_path, output_folder="tests", language="python", shot_type="zero_shot"):
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

if __name__ == "__main__":
    source_folder = "source_files"
    output_folder = "tests"
    os.makedirs(output_folder, exist_ok=True)

    # Process each Python file in the source folder and subfolders
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path, output_folder=output_folder, language="python", shot_type="few_shot")

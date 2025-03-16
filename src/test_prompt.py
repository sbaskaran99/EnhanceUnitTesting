
import os
import logging
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get the OpenAI API key from the environment
openai_api_key = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":
    prompt = """
    Create comprehensive edge-case unit test code for the following python class or functions:
    class PasswordValidationMixin1:
        MIN_LENGTH = 8
        oldpassword_model = None
        num_specialChar_regex = re.compile(r"[!@#$%^&*()_+\\-/=~]")
        numeric_regex = re.compile(r"\\d")
        uppercase_regex = re.compile(r"[A-Z]")
        lowercase_regex = re.compile(r"[a-z]")

        @staticmethod
        def is_password_matching(password, password2):
            return password == password2
        
        @staticmethod
        def is_first_alpha(password):
            validation = password[0].isalpha()
            msg = (
                None if validation
                else "The first letter of your password must be an alphabet!"
            )
            dict1 = {{"validation": validation, "msg": msg}}
            return dict1
    """

    try:
        client = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        prompt_template = PromptTemplate(template=prompt,input_variables=[])
        #prompt_template.input_variables = []
        print(prompt_template)
        functionality_chain = prompt_template | client
        functionality_tests_response = functionality_chain.invoke({})
        functionality_tests = functionality_tests_response.content.strip()
        print(functionality_tests)
    except Exception as e:
        logger.error(f"Error occurred: {e}")

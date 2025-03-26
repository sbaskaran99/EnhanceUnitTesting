import os
import subprocess
import autogen
import streamlit as st

# Define AI Agents
config_path = r"D:\Sai\EnhanceUnitTesting\src\agenticapp\OAI_CONFIG_LIST.json"
config_list = autogen.config_list_from_json(config_path)

generation_agent = autogen.AssistantAgent(
    name="TestGenerationAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

compilation_agent = autogen.AssistantAgent(
    name="CompilationAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

test_execution_agent = autogen.AssistantAgent(
    name="TestExecutionAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

coverage_agent = autogen.AssistantAgent(
    name="CoverageAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

improvement_agent = autogen.AssistantAgent(
    name="ImprovementAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

# Helper function to extract text from tuple responses
def extract_text(response):
    if isinstance(response, tuple):
        return response[1] if len(response) > 1 else response[0]
    return response

# Function to generate tests
def generate_tests(source_code):
    prompt = f"Generate unit tests for the following code:\n{source_code}"
    response = generation_agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
    return extract_text(response)

# Function to check compilation and fix errors
def check_and_fix_tests(test_code):
    prompt = f"Check the following test code for compilation issues and fix them:\n{test_code}"
    response = compilation_agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
    return extract_text(response)

# Function to execute tests and get results
def execute_tests(test_code):
    test_code = extract_text(test_code)  # Ensure it's a string
    
    if not isinstance(test_code, str):
        raise ValueError(f"Expected str, but got {type(test_code).__name__}: {test_code}")

    with open("temp_test.py", "w") as f:
        f.write(test_code)

    result = subprocess.run(["pytest", "--cov=temp_test.py", "--cov-report=xml"], capture_output=True, text=True)
    return result.stdout

# Function to measure code coverage
def measure_coverage():
    prompt = "Analyze the coverage report and suggest improvements."
    response = coverage_agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
    return extract_text(response)

# Function to improve coverage
def improve_coverage(source_code, current_coverage):
    prompt = f"Improve the test coverage for the following code:\n{source_code}\nCurrent coverage: {current_coverage}"
    response = improvement_agent.generate_oai_reply(messages=[{"role": "user", "content": prompt}])
    return extract_text(response)

# Streamlit UI
st.title("Automated Test Generation & Coverage Improvement")

uploaded_file = st.file_uploader("Upload Source Code File", type=["py"])
if uploaded_file:
    source_code = uploaded_file.read().decode("utf-8")
    st.code(source_code, language="python")

    if st.button("Generate & Run Tests"):
        try:
            st.write("⏳ Generating unit tests...")
            test_code = generate_tests(source_code)
            st.code(test_code, language="python")

            st.write("⏳ Checking and fixing test compilation issues...")
            fixed_test_code = check_and_fix_tests(test_code)
            st.code(fixed_test_code, language="python")

            st.write("⏳ Executing tests...")
            test_results = execute_tests(fixed_test_code)

            st.write("⏳ Measuring initial test coverage...")
            initial_coverage = measure_coverage()

            st.write("⏳ Improving test coverage...")
            improved_tests = improve_coverage(source_code, initial_coverage)
            st.code(improved_tests, language="python")

            st.write("⏳ Executing improved tests...")
            improved_results = execute_tests(improved_tests)

            st.write("⏳ Measuring improved test coverage...")
            improved_coverage = measure_coverage()

            # Display results in expandable sections
            with st.expander("Test Results"):
                st.text(test_results)
            
            with st.expander("Initial Coverage"):
                st.text(initial_coverage)

            with st.expander("Improved Test Results"):
                st.text(improved_results)

            with st.expander("Improved Coverage"):
                st.text(improved_coverage)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

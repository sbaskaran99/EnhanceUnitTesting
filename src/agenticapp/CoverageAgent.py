import coverage
import pandas as pd
# Start coverage before importing other modules
cov = coverage.Coverage(omit=["*/tests/*", "*/__init__.py"], include=["*/source_files/*"])
cov.start()
import autogen
from autogen import AssistantAgent, config_list_from_json
import unittest
import os
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

coverage_agent = AssistantAgent(
    name="CoverageAgent",
    llm_config={"config_list": config_list, "temperature": 0},
)

def measure_coverage(test_folder, coverage_report_file="coverage_report.txt"):
    """
    Uses coverage_agent to measure test coverage and generate reports.
    """
    print("CoverageAgent: Measuring test coverage...")

    coverage_agent.generate_reply(
    messages=[{"role": "system", "content": "Measure code coverage automatically and return results."}]
    )
    
    loader = unittest.defaultTestLoader
    topleveldir="D:\\Sai\\EnhanceUnitTesting\\tests"
    suite = loader.discover(test_folder, pattern="test_*.py",top_level_dir=topleveldir)
    if suite.countTestCases() == 0:
        print("No test cases found in the specified folder.")
        return
    result=unittest.TextTestRunner().run(suite)
    
    cov.stop()
    cov.save()

    with open(coverage_report_file, "w") as f:
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
                if len(parts) >= 4:
                    data.append(parts)

        if data:
            #df = pd.DataFrame(data, columns=["File", "Statements", "Missed","Branch", "BrPart", "Coverage"])
            df = pd.DataFrame(data, columns=["File", "Statements", "Missed", "Coverage"])
            df["Coverage"] = df["Coverage"].str.replace("%", "").astype(float)  # Convert coverage to numeric

        return df   

if __name__ == "__main__":
    test_folder = "./tests"
    import os
    print(os.listdir(test_folder))

    # Execute tests and measure coverage automatically
    
    measure_coverage(test_folder)

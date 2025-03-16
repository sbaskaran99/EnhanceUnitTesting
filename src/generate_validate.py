import subprocess
import logging
import os
import streamlit as st
import zipfile
import tempfile
import shutil
import pandas as pd
from generate_tests import process_file
#from generate_tests_grok import process_file
from parseCoverage import parse_coverage_report
from generate_additionaltests import generate_and_update_tests
from generate_testresults import discover_and_run_tests
from utils.file_utils import  create_output_folder,extract_zip_file
# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define paths
SOURCE_FOLDER_PATH = r"D:\Sai\UnitTesting-LangChain\source_files"
TEST_FOLDER_PATH = r"D:\Sai\UnitTesting-LangChain\tests"
RESULTS_FILE_PATH = r"D:/Sai/UnitTesting-LangChain/results.html"
COVERAGE_REPORT_PATH = "coverage_report.txt"


def process_source_files(source_folder, test_folder):
    """Process each Python file in the source folder and its subfolders."""
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                process_file(file_path, output_folder=test_folder, language="python", shot_type="few_shot")

def run_tests_with_coverage(test_directory):
    """Run the tests with coverage, handling timeouts and errors."""
    test_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(test_directory)
        for file in files if file.startswith("test_") and file.endswith(".py") and file not in ("__init__.py",)
    ]
    coverage_data_dir = ".coverage_data"
    os.makedirs(coverage_data_dir, exist_ok=True)

    for test_file in test_files:
        try:
            coverage_file = os.path.join(coverage_data_dir, f".coverage.{os.path.basename(test_file)}")
            subprocess.run([
                "coverage", "run", "--branch", f"--data-file={coverage_file}",
                "--source=source_files", test_file
            ], timeout=15, check=True)
            logger.info(f"Test {test_file} completed successfully.")
        except subprocess.TimeoutExpired:
            logger.error(f"Test {test_file} timed out (15 seconds).")
        except subprocess.CalledProcessError as e:
            logger.error(f"Test {test_file} failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {test_file}: {e}")

    try:
        subprocess.run(["coverage", "combine", coverage_data_dir], check=True)
        subprocess.run(["coverage", "report"], check=True)
        logger.info("Coverage report generated successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Coverage report generation failed: {e}")
    
    # Cleanup
    shutil.rmtree(coverage_data_dir, ignore_errors=True)
    logger.info("Temporary coverage data cleaned up.")

def generate_coverage_report_file(filename):
    """Generate a coverage report excluding test files."""
    with open(filename, "w") as coverage_file:
        subprocess.run(["coverage", "report", "--omit=*/tests/*"], stdout=coverage_file, stderr=subprocess.STDOUT)
    
def parse_low_coverage_files():
    """Parse coverage report for low-coverage files."""
    return parse_coverage_report(COVERAGE_REPORT_PATH)


def copy_source_files(source_folder):
    """Copy the source files to the SOURCE_FOLDER_PATH."""
    if os.path.exists(SOURCE_FOLDER_PATH):
        shutil.rmtree(SOURCE_FOLDER_PATH)  # Remove existing files
    shutil.copytree(source_folder, SOURCE_FOLDER_PATH)
    st.write(f"✅ Source files copied to: `{SOURCE_FOLDER_PATH}`")

def display_coverage_report():
    """Read and display coverage report in a tabular format."""
    if os.path.exists(COVERAGE_REPORT_PATH):
        with open(COVERAGE_REPORT_PATH, "r") as f:
            lines = f.readlines()

        # Extract table-like data
        data = []
        for line in lines:
            if "%" in line:  # Look for coverage percentage lines
                parts = line.split()
                if len(parts) >= 5:
                    data.append(parts)

        if data:
            df = pd.DataFrame(data, columns=["File", "Statements", "Missed","Branch", "BrPart", "Coverage"])
            df["Coverage"] = df["Coverage"].str.replace("%", "").astype(float)  # Convert coverage to numeric

            # Display as table
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df)

def main():
    # Streamlit UI
    st.title('Effective Unit Testing Using LLMs')
     
    # File uploader for zip file
    uploaded_zip = st.file_uploader("Choose a zip file containing the source folder", type=["zip"])

    if uploaded_zip:
        # Extract the zip file and get the folder path
        source_folder = extract_zip_file(uploaded_zip)
               
        # Copy source files to the designated folder
        copy_source_files(source_folder)

        # Get the first-level subdirectory inside SOURCE_FOLDER_PATH
        subfolders = [f.name for f in os.scandir(SOURCE_FOLDER_PATH) if f.is_dir()]
        root_folder = subfolders[0] if subfolders else None  # Handle case if no subfolders exist
        test_directory = os.path.join(TEST_FOLDER_PATH, root_folder) if root_folder else TEST_FOLDER_PATH
        os.makedirs(test_directory, exist_ok=True)

        if st.button('🚀 Generate Unit TestCases'):
            create_output_folder(test_directory)
           
            # Process the source files and create tests
            process_source_files(SOURCE_FOLDER_PATH, TEST_FOLDER_PATH)

            # Run the tests with coverage
            #run_tests_with_coverage(test_directory)

            # Discover and run the tests
            output_json = "results.json"
            output_html = "results.html"
            discover_and_run_tests(test_directory, output_json, output_html)

            # Generate the coverage report
            #generate_coverage_report_file(COVERAGE_REPORT_PATH)

            # Show test results
            st.subheader("📄 View Test Results")
            st.markdown(f"[Click here to open results](file:///{RESULTS_FILE_PATH})", unsafe_allow_html=True)
        
            # Display coverage report in tabular format
            #display_coverage_report()

            # Uncomment to handle low coverage files
            # low_coverage_files = parse_low_coverage_files()
            # if low_coverage_files:
            #     generate_and_update_tests(low_coverage_files, test_directory)
            #     run_tests_with_coverage(test_directory)
            #     generate_coverage_report_file("coverage_report_updated.txt")

if __name__ == "__main__":
    main()

import subprocess
import logging
import os
import streamlit as st
import zipfile
import tempfile
import shutil
import shutil
import os



from TestGenerationAgent import process_file
#from generate_tests_grok import process_file
from parseCoverage import parse_coverage_report
from generate_additionaltests import generate_and_update_tests
from TestExecutionAgent import discover_and_run_tests
from CoverageAgent import measure_coverage,display_coverage_report
from  AutoFixingAgent import fix_failing_tests
from utils.file_utils import  create_output_folder,extract_zip_file,clear_directories
# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define paths
SOURCE_FOLDER_PATH = r"D:\Sai\EnhanceUnitTesting\source_files"
TEST_FOLDER_PATH = r"D:\Sai\EnhanceUnitTesting\tests"
RESULTS_FILE_PATH = r"D:/Sai/EnhanceUnitTesting/results.html"
FIXED_TESTCASERESULTS_PATH=r"D:/Sai/EnhanceUnitTesting/fixed_testcaseresults.html"
COVERAGE_REPORT_PATH = "coverage_report.txt"
CACHE_PATH = r"D:\\Sai\\EnhanceUnitTesting\\.cache"

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
        subprocess.run(["coverage", "report", "--omit=*//mnt/data/final_tests/*"], stdout=coverage_file, stderr=subprocess.STDOUT)
    
def parse_low_coverage_files():
    """Parse coverage report for low-coverage files."""
    return parse_coverage_report(COVERAGE_REPORT_PATH)


def copy_source_files(source_folder):
    """Copy the source files to the SOURCE_FOLDER_PATH."""
    if os.path.exists(SOURCE_FOLDER_PATH):
        shutil.rmtree(SOURCE_FOLDER_PATH)  # Remove existing files
    shutil.copytree(source_folder, SOURCE_FOLDER_PATH)
    st.write(f"✅ Source files copied to: `{SOURCE_FOLDER_PATH}`")

import streamlit as st
import os

def main():
    st.title('Enhance Unit Testing Using LLMs')

    # Initialize session state variables
    if "test_generated" not in st.session_state:
        st.session_state.test_generated = False  # Track if test cases were generated
    if "test_fixed" not in st.session_state:
        st.session_state.test_fixed = False  # Track if test case issues were fixed

    uploaded_zip = st.file_uploader("Choose a zip file containing the source folder", type=["zip"])

    if uploaded_zip:
        source_folder = extract_zip_file(uploaded_zip)
        copy_source_files(source_folder)

        subfolders = [f.name for f in os.scandir(SOURCE_FOLDER_PATH) if f.is_dir()]
        root_folder = subfolders[0] if subfolders else None
        test_directory = os.path.join(TEST_FOLDER_PATH, root_folder) if root_folder else TEST_FOLDER_PATH
        os.makedirs(test_directory, exist_ok=True)

        if st.button('🚀 Generate Unit TestCases'):
            create_output_folder(test_directory)
            process_source_files(SOURCE_FOLDER_PATH, TEST_FOLDER_PATH)
            discover_and_run_tests(TEST_FOLDER_PATH, "results.json", "results.html")
            measure_coverage(TEST_FOLDER_PATH)

            st.session_state.test_generated = True
            st.rerun()

    # Ensure results are **always visible** if tests were generated
    if st.session_state.test_generated:
        st.subheader("📄 View Test Results")
        st.markdown(f"[Click here to open results](file:///{RESULTS_FILE_PATH})", unsafe_allow_html=True)
        df=display_coverage_report(COVERAGE_REPORT_PATH)
        # Display as table
        st.subheader("📊 Test Coverage Report")
        st.dataframe(df)
        if st.button("⏳ Fix Test case issues..."):
            st.write("Fix Test Case button clicked!")  # Debugging
            # Clear cache before fixing test cases
 
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            st.cache_data.clear()
            st.cache_resource.clear()
           
            fix_failing_tests()
            
            # Remove only the .cache folder
            if os.path.exists(CACHE_PATH):
                shutil.rmtree(CACHE_PATH, ignore_errors=True)
                st.write(f"Deleted cache folder: {CACHE_PATH}")  # Debugging
            discover_and_run_tests("./tests", "fixed_testcaseresults.json", "fixed_testcaseresults.html")
            measure_coverage(TEST_FOLDER_PATH)

            st.session_state.test_fixed = True
            st.rerun()

    # Ensure improved test results **always** appear after fixing issues
    if st.session_state.test_fixed:
        with st.expander("🔧 Improved Test Cases"):
            st.subheader("📄 View Test Results")
            st.markdown(f"[Click here to open results](file:///{FIXED_TESTCASERESULTS_PATH})", unsafe_allow_html=True)
            df=display_coverage_report(COVERAGE_REPORT_PATH)
            # Display as table
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df)
            if st.button("🚀 Deploy Again"):
                st.success("✅ Deployment initiated successfully!")

            # Uncomment to handle low coverage files
            # low_coverage_files = parse_low_coverage_files()
            # if low_coverage_files:
            #     generate_and_update_tests(low_coverage_files, test_directory)
            #     run_tests_with_coverage(test_directory)
            #     generate_coverage_report_file("coverage_report_updated.txt")

if __name__ == "__main__":
    main()

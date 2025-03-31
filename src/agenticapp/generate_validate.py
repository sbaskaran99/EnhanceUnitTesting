import subprocess
import logging
import os
import streamlit as st
import zipfile
import tempfile
import shutil
from TestGenerationAgent import process_file  # Process each source file for test generation
from TestExecutionAgent import discover_and_run_tests
from CoverageAgent import measure_coverage, display_coverage_report, generate_and_update_tests
from AutoFixingAgent import fix_failing_tests
from utils.file_utils import create_output_folder, extract_zip_file, clear_directories

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define paths
SOURCE_FOLDER_PATH = r"D:\Sai\EnhanceUnitTesting\source_files"
TEST_FOLDER_PATH = r"D:\Sai\EnhanceUnitTesting\tests"
RESULTS_FILE_PATH = r"D:/Sai/EnhanceUnitTesting/results.html"
FIXED_TESTCASERESULTS_PATH = r"D:/Sai/EnhanceUnitTesting/fixed_testcaseresults.html"
IMPROVED_TESTCASERESULTS_PATH = r"D:/Sai/EnhanceUnitTesting/improved_testcaseresults.html"
COVERAGE_REPORT_PATH = "coverage_report.txt"
CACHE_PATH = r"D:\Sai\EnhanceUnitTesting\.cache"

def process_source_files(source_folder, test_folder):
    """Process each Python file in the source folder and its subfolders."""
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                process_file(file_path, output_folder=test_folder, language="python", shot_type="few_shot")

def copy_source_files(source_folder):
    """Copy the source files to the SOURCE_FOLDER_PATH."""
    if os.path.exists(SOURCE_FOLDER_PATH):
        shutil.rmtree(SOURCE_FOLDER_PATH)  # Remove existing files
    shutil.copytree(source_folder, SOURCE_FOLDER_PATH)
    st.write(f"✅ Source files copied to: `{SOURCE_FOLDER_PATH}`")

def main():
    st.title('Enhance Unit Testing Using LLMs')

    # Initialize session state variables if not already present.
    if "test_generated" not in st.session_state:
        st.session_state.test_generated = False
    if "test_fixed" not in st.session_state:
        st.session_state.test_fixed = False
    if "coverage_improvement" not in st.session_state:
        st.session_state.coverage_improvement = False

    uploaded_zip = st.file_uploader("Choose a zip file containing the source folder", type=["zip"])
    if uploaded_zip:
        source_folder = extract_zip_file(uploaded_zip)
        copy_source_files(source_folder)

        # Assume that the source folder structure contains one root subfolder.
        subfolders = [f.name for f in os.scandir(SOURCE_FOLDER_PATH) if f.is_dir()]
        root_folder = subfolders[0] if subfolders else None
        test_directory = os.path.join(TEST_FOLDER_PATH, root_folder) if root_folder else TEST_FOLDER_PATH
        os.makedirs(test_directory, exist_ok=True)

        if st.button('🚀 Generate Unit TestCases'):
            create_output_folder(test_directory)
            process_source_files(SOURCE_FOLDER_PATH, TEST_FOLDER_PATH)
            # Run tests and generate initial coverage report.
            discover_and_run_tests(TEST_FOLDER_PATH, "results.json", RESULTS_FILE_PATH)
            measure_coverage(TEST_FOLDER_PATH,COVERAGE_REPORT_PATH)
            st.session_state.test_generated = True
            st.rerun()

    if st.session_state.test_generated:
        st.subheader("📄 View Test Results")
        st.markdown(f"[Click here to open results](file:///{RESULTS_FILE_PATH})", unsafe_allow_html=True)
        df = display_coverage_report(COVERAGE_REPORT_PATH)
        st.subheader("📊 Test Coverage Report")
        st.dataframe(df)

        if st.button("⏳ Fix Test case issues..."):
            st.write("Fix Test Case button clicked!")  # Debugging output
            # Clear session state and caches before fixing tests.
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.cache_data.clear()
            st.cache_resource.clear()
            fix_failing_tests()
            if os.path.exists(CACHE_PATH):
                shutil.rmtree(CACHE_PATH, ignore_errors=True)
                st.write(f"Deleted cache folder: {CACHE_PATH}")
            discover_and_run_tests("./tests", "fixed_testcaseresults.json", FIXED_TESTCASERESULTS_PATH)
            measure_coverage(TEST_FOLDER_PATH,COVERAGE_REPORT_PATH)
            st.session_state.test_fixed = True
            st.rerun()

    if st.session_state.test_fixed:
        with st.expander("🔧 Fixed Test Cases"):
            st.subheader("📄 View Fixed Test Results")
            st.markdown(f"[Click here to open fixed test results](file:///{FIXED_TESTCASERESULTS_PATH})", unsafe_allow_html=True)
            df = display_coverage_report(COVERAGE_REPORT_PATH)
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df)
            if st.button("🚀 Improve Coverage"):
                generate_and_update_tests(COVERAGE_REPORT_PATH, TEST_FOLDER_PATH)
                discover_and_run_tests("./tests", "improved_testcaseresults.json", IMPROVED_TESTCASERESULTS_PATH)
                measure_coverage(TEST_FOLDER_PATH, COVERAGE_REPORT_PATH,should_restart=True)
                st.session_state.coverage_improvement = True# New state
                st.rerun()
    
    if st.session_state.coverage_improvement:
        with st.expander("🔧 Improved Test Cases"):
            st.subheader("📄 View Test Results")
            st.markdown(f"[Click here to open results](file:///{IMPROVED_TESTCASERESULTS_PATH})", unsafe_allow_html=True)
            df = display_coverage_report(COVERAGE_REPORT_PATH)
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df)

            if st.button("🚀 Deploy Again"):
                st.success("✅ Deployment initiated successfully!")

if __name__ == "__main__":
    main()

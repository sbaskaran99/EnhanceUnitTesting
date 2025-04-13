import logging
import os
import streamlit as st
import shutil
from TestGenerationAgent import process_file  # Process each source file for test generation
from TestExecutionAgent import discover_and_run_tests
from CoverageAgent import measure_coverage, display_coverage_report, generate_and_update_tests,measure_coverage_with_cli
from AutoFixingAgent import fix_failing_tests
from utils.file_utils import create_output_folder, extract_zip_file, clear_directories
from MutationTestAgent import get_mutation_coverage,run_mutation_tests
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
IMPROVED_COVERAGE_REPORT_PATH = "coverage_report1.txt"
FIXED_COVERAGE_REPORT_PATH = "coverage_report2.txt"
CACHE_PATH = r"D:\Sai\EnhanceUnitTesting\.cache"
TEST_RESULTS_FILE = "results.json"
IMPROVED_TEST_RESULTS_FILE = "improved_testcaseresults.json"

# Mutation Test Path configurations
APP_NAME = "InsuranceApp_Modified"
MuUTATION_TEST_FOLDER_PATH = os.path.join(r"D:\Sai\EnhanceUnitTesting\tests", APP_NAME)
MUTATION_SOURCE_FOLDER_PATH = os.path.join(r"D:\Sai\EnhanceUnitTesting\source_files", APP_NAME)
MUTATION_COVERAGE_DIR= r"D:/Sai/EnhanceUnitTesting/mutation_coverage"
MUTATION_REPORT_HTML = os.path.join(MUTATION_COVERAGE_DIR, "index.html")
MUTAITON_PROJECT_ROOT = r"D:\Sai\EnhanceUnitTesting"
# Module paths for mut.py
target_module = f"source_files.{APP_NAME}"
test_module = f"tests.{APP_NAME}"

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
    if "mutation_test" not in st.session_state:
        st.session_state.mutation_test = False   
    # Initialize session state for mutation stats
    if "mutation_stats" not in st.session_state:
        st.session_state.mutation_stats = {
            "mutation_score": 0.0,
            "killed": 0,
            "survived": 0,
         "total": 0
        }
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
        if st.button("🚀 Improve Coverage"):
            generate_and_update_tests(COVERAGE_REPORT_PATH, TEST_FOLDER_PATH)
            discover_and_run_tests("./tests", IMPROVED_TEST_RESULTS_FILE, IMPROVED_TESTCASERESULTS_PATH)
            measure_coverage_with_cli(TEST_FOLDER_PATH, IMPROVED_COVERAGE_REPORT_PATH)
            st.session_state.coverage_improvement = True# New state
            st.rerun()
    
    if st.session_state.coverage_improvement:
        with st.expander("🔧 Improved Test Cases"):
            st.subheader("📄 View Test Results")
            st.markdown(f"[Click here to open results](file:///{IMPROVED_TESTCASERESULTS_PATH})", unsafe_allow_html=True)
            df = display_coverage_report(IMPROVED_COVERAGE_REPORT_PATH)
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df)
            if st.button('🚀 Fix Unit TestCases'):
                fix_failing_tests(IMPROVED_TEST_RESULTS_FILE)
                discover_and_run_tests("./tests", "fixed_testcaseresults.json", FIXED_TESTCASERESULTS_PATH)
                measure_coverage_with_cli(TEST_FOLDER_PATH, FIXED_COVERAGE_REPORT_PATH)
                st.session_state.test_fixed = True
                st.rerun()
    if st.session_state.test_fixed:
        with st.expander("🔧 Fixed Test Cases"):
            st.subheader("📄 View Fixed Test Results")
            st.markdown(f"[Click here to open fixed test results](file:///{FIXED_TESTCASERESULTS_PATH})", unsafe_allow_html=True)
            df = display_coverage_report(FIXED_COVERAGE_REPORT_PATH)
            st.subheader("📊 Test Coverage Report")
            st.dataframe(df) 
            if st.button('🚀 Measure Mutation Coverage'):
                coverage_before, stats_before = get_mutation_coverage(MUTAITON_PROJECT_ROOT, target_module, test_module, 'before')
                st.session_state.mutation_stats = stats_before
                st.session_state.mutation_test = True
                st.rerun()  

    
    if st.session_state.mutation_test:
        with st.expander("🔧 Mutation Coverage"):
            st.subheader("📊 Mutation Test Results")
            
            # Create columns for layout
            col1, col2 = st.columns([1, 1])
            
            # Add metrics in first column
            with col1:
                stats = st.session_state.mutation_stats
                st.metric(
                    label="🎯 Mutation Score",
                    value=f"{stats['mutation_score']:.1f}%",
                    delta=f"{stats['killed']} killed mutants"
                )
            
            # Add detailed stats in second column
            with col2:
                progress = stats['killed'] / stats['total'] if stats['total'] > 0 else 0
                st.progress(progress)
                
            # Create a styled table using markdown
            st.markdown("""
            | Metric | Value |
            |--------|-------|
            | 🎯 **Mutation Score** | {score:.1f}% |
            | ✅ **Killed Mutants** | {killed} |
            | ❌ **Survived Mutants** | {survived} |
            | 📊 **Total Mutants** | {total} |
            """.format(
                score=stats['mutation_score'],
                killed=stats['killed'],
                survived=stats['survived'],
                total=stats['total']
            ))
            
            # Add a visual indicator of test quality
            quality_score = stats['mutation_score']
            if quality_score >= 80:
                st.success("🌟 Excellent mutation coverage!")
            elif quality_score >= 60:
                st.warning("⚠️ Good coverage, but room for improvement")
            else:
                st.error("❗ Coverage needs significant improvement")
                
          
        # Add view report section with better error handling
            st.markdown("### 📊 View Full Report")
            if os.path.exists(MUTATION_REPORT_HTML):
                st.markdown(
                    f'<a href="file:///{MUTATION_REPORT_HTML}" target="_blank">'
                    '🔍 Click here to view detailed mutation report</a>', 
                    unsafe_allow_html=True
                )
            else:
                st.warning("⚠️ Mutation report not generated yet at: " + MUTATION_REPORT_HTML)         
                # Add improvement suggestions if needed
                if stats['survived'] > 0:
                    st.info("""
                    💡 **Improvement Suggestions:**
                    - Add tests for the {survived} surviving mutants
                    - Focus on edge cases and boundary conditions
                    - Consider adding negative test scenarios
                    """.format(survived=stats['survived']))
                
            if st.button("🚀 Deploy Again", type="primary"):
                st.success("✅ Deployment initiated successfully!")
                st.balloons()    
if __name__ == "__main__":
    main()

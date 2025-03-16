import unittest
import os
import json
from datetime import datetime
import pandas as pd
import importlib.util
import subprocess
import coverage
def discover_and_run_tests(test_folder, output_json="test_results.json", output_html="test_results.html"):
    """
    Discovers and runs all unit tests in a specific folder.
    Stores the test results in a JSON file and generates an HTML report.

    :param test_folder: The folder containing the test files.
    :param output_json: The output file to store the test results in JSON format.
    :param output_html: The output file to store the test results in HTML format.
    """
    coverage_file="coverage_report.txt"
    # Start coverage measurement with exclusions
    cov = coverage.Coverage(
        omit=[
            "*/tests/*",  # Exclude all test files
            "*/__init__.py",  # Exclude all __init__.py files
            "src/generate_testresults.py"
        ]
    )
    
    
    cov.start()
    #test_files = [f for f in os.listdir(test_folder) if f.endswith('.py')]
    #print("Discovered test files:", test_files)

     # Recursively find all Python test files in the test_folder and subfolders
    test_files = []
    for root, dirs, files in os.walk(test_folder):
        for file in files:
            if file.endswith('.py') and file.startswith('test_'):  # only consider test files
                test_files.append(os.path.join(root, file))
    
    print("Discovered test files:", test_files)

    if not test_files:
        print("No test files found.")
        return
    print("TestFolder",test_folder)
    loader = unittest.defaultTestLoader
    topleveldir="D:\\Sai\\UnitTesting-LangChain\\tests"
    suite = loader.discover(test_folder, pattern="test_*.py",top_level_dir=topleveldir)
    #suite = loader.discover(test_folder, pattern="test_*.py",top_level_dir=test_folder)
    if suite.countTestCases() == 0:
        print("No test cases found in the current folder.")
        return
    results = {
        "test_run_date": datetime.now().isoformat(),
        "results": []
    }

    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(suite)
    print(result)
    #suite = unittest.TestLoader().discover(test_folder,pattern="test_*.py",top_level_dir=test_folder)
    suite = unittest.TestLoader().discover(test_folder,pattern="test_*.py",top_level_dir=topleveldir)
    if suite.countTestCases() == 0:
        print("No test cases found in the specified folder.")
        return
    
    all_test_cases = []
    _collect_test_cases(suite, all_test_cases)
    print(f"✅ Collected {len(all_test_cases)} test cases after recursion.")
    
    for test_case in all_test_cases: # loop over test cases and add results
        add_test_result(results["results"], test_case, result)
   
    with open(output_json, "w") as f:
        json.dump(results, f, indent=4)
    generate_html_report(results["results"], output_html)
    # Stop coverage and save report
    cov.stop()
    cov.save()

    # Generate coverage report
    with open(coverage_file, "w") as f:
        cov.report(file=f)
    # Generate and store the coverage report in an HTML file
    cov.html_report(directory="coverage_html_report")    
    # Optionally, generate a simple text report for the console
   #cov.report(omit="*/tests/*")
   # print(f"Coverage report saved to {coverage_file}")

def _collect_test_cases(test_or_suite, all_test_cases):
    """ Recursively collects test cases from a suite or individual test case. """
    if isinstance(test_or_suite, unittest.TestSuite):
        for test in test_or_suite:
            _collect_test_cases(test, all_test_cases)  # Recursively process nested suites
    elif isinstance(test_or_suite, unittest.TestCase):
        print(f"✔️ Collected test: {test_or_suite.id()}")  # Debugging statement
        all_test_cases.append(test_or_suite)  # Store test cases


def add_test_result(results_list, test, result):
    test_id = test.id()  # Get the test ID

    status = "PASS"  # Assume PASS initially
    reason = None

    for failed_test, failure_reason in result.failures:
        if failed_test.id() == test_id:  # Compare test IDs
            status = "FAIL"
            reason = str(failure_reason)
            break # Exit the inner loop once found
    else:  # No failure found for this test
        for error_test, error_reason in result.errors:
            if error_test.id() == test_id:  # Compare test IDs
                status = "ERROR"
                reason = str(error_reason)
                break  # Exit the inner loop once found
        else:  # No error found for this test
            for skipped_test, skip_reason in result.skipped:
                if skipped_test.id() == test_id:  # Compare test IDs
                    status = "SKIP"
                    reason = str(skip_reason)
                    break # Exit the inner loop once found

    results_list.append({
        "file": str(test.__module__),
        "method": str(test),
        "status": status,
        "reason": reason
    })


def generate_html_report(test_results, output_file):
    """
    Generate a beautified HTML report with test results in a tabular format.
    
    :param test_results: List of test results.
    :param output_file: The file to store the HTML report.
    """
    # Create a DataFrame for easy HTML generation
    df = pd.DataFrame(test_results)

    # Add custom styles for pass/fail/error rows
    def apply_status_color(row):
        if row['status'] == 'PASS':
            return ['background-color: #d4edda;' for _ in row]  # Green background for PASS
        elif row['status'] == 'FAIL':
            return ['background-color: #f8d7da;' for _ in row]  # Red background for FAIL
        elif row['status'] == 'ERROR':
            return ['background-color: #fff3cd;' for _ in row]  # Yellow background for ERROR
        return []

    # Applying custom colors
    df_style = df.style.apply(apply_status_color, axis=1)

    # Generate HTML content for the report using to_html() instead of render()
    html_content = df_style.to_html()

    # Add CSS to style the HTML report
    html_template = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                text-align: left;
            }}
            th, td {{
                padding: 12px;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f4f4f4;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .reason {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <h2>Unit Test Results</h2>
        <p>Test run date: {datetime.now().isoformat()}</p>
        {html_content}
    </body>
    </html>
    """

    # Save the HTML content to the output file
    with open(output_file, "w") as f:
        f.write(html_template)

    print(f"Test results stored in {output_file}")

def generate_coverage_report_file(filename):
    """Generate a coverage report excluding test files."""
    with open(filename, "w") as coverage_file:
        subprocess.run(["coverage", "report", "--omit=*/tests/*"], stdout=coverage_file, stderr=subprocess.STDOUT)
    
if __name__ == "__main__":
    # Specify the folder where your test files are located
    test_folder = "./tests"  # Replace with the path to your test folder
    COVERAGE_REPORT_PATH = "coverage_report.txt"
    # Specify the output files for test results
    output_json = "unit_test_results.json"
    output_html = "unit_test_results.html"

    # Run the tests and save results in both JSON and HTML formats
    discover_and_run_tests(test_folder, output_json, output_html)
    # Generate the coverage report
    #generate_coverage_report_file(COVERAGE_REPORT_PATH)




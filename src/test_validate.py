
import os 
import pandas as pd
#from parseCoverage import parse_coverage_report,find_test_file
#from generate_additionaltests import generate_and_update_tests

def display_coverage_report(file_path):
    """Read and display coverage report in a tabular format."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Extract table-like data
        data = []
        for line in lines:
            if "%" in line:  # Look for coverage percentage lines
                parts = line.split()
                print(parts)
                if len(parts) >= 5:
                    data.append(parts)
        print(data)
        if data:
            df = pd.DataFrame(data, columns=["File", "Statements", "Missed","Branch", "BrPart", "Coverage"])
            df["Coverage"] = df["Coverage"].str.replace("%", "").astype(float)  # Convert coverage to numeric

        return df  


if __name__ == "__main__":
    # Get the current directory
    current_directory = os.getcwd()

    # Construct the full path for 'coverage_report.txt'
    file_path = os.path.join(current_directory, "coverage_report.txt")
   
    # Print the path (optional, for debugging)
    print(f"File path: {file_path}")
    df1=display_coverage_report(file_path)
    #print(df1)
    #low_coverage_files = parse_coverage_report(file_path)
    #print("\nFiles with less than 100% coverage:")
    #for file, coverage in low_coverage_files:
       # print(f"{file} - {coverage}% coverage")
    #test_dir = "D:\\Sai\\UnitTesting-LangChain\\tests\\arrays"
    #generate_and_update_tests(low_coverage_files, test_dir)

    
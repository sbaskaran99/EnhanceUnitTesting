Please execute the following shell script in your project directory to generate the coverage report. This will help us analyze the current test coverage and identify areas that need improvement.

```sh
# Install coverage if it's not already installed
pip install coverage

# Run coverage analysis
coverage run -m pytest  # or replace 'pytest' with your test runner

# Generate an HTML report
coverage html

# This will create an 'htmlcov' directory containing the report
echo "Report generated in htmlcov/index.html"
```

After executing these commands, please check the `htmlcov/index.html` file to view the coverage report. Let me know once you have the coverage details, and we can proceed with improving the test coverage.
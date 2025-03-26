import unittest
import coverage

# Start coverage analysis
cov = coverage.Coverage(branch=True, source=["source_files/arrays"])
cov.start()

# Discover and run tests
loader = unittest.TestLoader()
suite = loader.discover(start_dir="tests/arrays")
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Stop coverage and save report
cov.stop()
cov.save()

# Generate coverage reports
cov.report(show_missing=True)
cov.html_report(directory="htmlcov")

# Print test summary
print("\nTest Results Summary:")
print(f"Tests Run: {result.testsRun}")
print(f"Errors: {len(result.errors)}")
print(f"Failures: {len(result.failures)}")

# Print details of errors and failures
if result.errors or result.failures:
    print("\nDetails:")
    for test, traceback in result.errors + result.failures:
        print(f"Test: {test}")
        print(f"Traceback: {traceback}")

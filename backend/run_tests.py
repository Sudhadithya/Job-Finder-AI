import os
import sys
import unittest

def main():
    # Add backend/ to python path so that app/ imports work correctly
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
        
    print(f"Running test suite in {backend_dir}...")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir=os.path.join(backend_dir, "tests"), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(tests)
    
    # Exit with code 0 if tests passed, 1 if failed
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()

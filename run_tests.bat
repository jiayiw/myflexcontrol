@echo off
echo =========================================
echo FlexRadio 6400 Control - Test Suite
echo =========================================
echo.

if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing test dependencies...
pip install -r requirements-test.txt

echo.
echo =========================================
echo Running all tests...
echo =========================================
pytest tests\ -v --cov=. --cov-report=term-missing --cov-report=html

echo.
echo =========================================
echo Running unit tests...
echo =========================================
pytest tests\unit\ -v

echo.
echo =========================================
echo Running integration tests...
echo =========================================
pytest tests\integration\ -v -m integration

echo.
echo =========================================
echo Running fast tests (excluding slow tests)...
echo =========================================
pytest tests\ -v -m "not slow"

echo.
echo =========================================
echo Test Summary
echo =========================================
echo Test coverage report generated: htmlcov\index.html
echo Open in browser: start htmlcov\index.html
echo.

deactivate
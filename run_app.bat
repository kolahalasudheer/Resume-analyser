@echo off
echo ==========================================
echo  ATS Forge - Starting Web Application
echo ==========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Installing/checking Streamlit...
pip install streamlit --quiet
echo.
echo Starting application...
echo Opening in your browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
streamlit run app.py

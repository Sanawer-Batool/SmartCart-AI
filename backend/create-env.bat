@echo off
REM Script to create .env file with your API key

echo Creating .env file...

(
echo GOOGLE_API_KEY=AIzaSyADh8OOzgqaxnbvAtjcyt32d8RGqSaYyqE
echo HOST=0.0.0.0
echo PORT=8000
echo DEBUG=True
echo HEADLESS=True
echo BROWSER_TIMEOUT=30000
) > .env

echo.
echo ✅ .env file created successfully!
echo.
echo Contents:
type .env
echo.
echo 🚀 Now restart the backend server with: python app.py
pause


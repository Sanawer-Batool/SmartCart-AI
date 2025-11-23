# Start SmartCart AI Backend Server
$BackendPath = "D:\All Projects\SmartCart AI\backend"
Set-Location $BackendPath
& "$BackendPath\venv\Scripts\Activate.ps1"
& "$BackendPath\venv\Scripts\python.exe" "$BackendPath\app.py"


# Start the Flask API server for the frontend


# Start the Flask API server for the frontend in the current PowerShell window, using the venv
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$jobQueueDir = Join-Path $scriptPath '..\src\job_queue'
$venvActivate = Join-Path $scriptPath '..\.venv\Scripts\Activate.ps1'

cd $jobQueueDir
. $venvActivate
python api_server.py


param(
    [int]$workers = 1
)

$redisPath = "C:\Program Files\Redis\redis-server.exe"
$jobQueueDir = "..\src\job_queue"
$venvActivate = "..\.venv\Scripts\Activate.ps1"
$pidDir = Join-Path $PSScriptRoot 'tmp'
if (-not (Test-Path $pidDir)) { New-Item -ItemType Directory -Path $pidDir | Out-Null }
$pidFile = Join-Path $pidDir 'auqa-pids.txt'
# Clear PID file at start
if (Test-Path $pidFile) { Remove-Item $pidFile }

# Start Redis server in new PowerShell window with -PROCESS AUQA marker
${p1} = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "[console]::Title = 'AUQA-REDIS'; & redis-server" -WindowStyle Normal -PassThru
Add-Content $pidFile $p1.Id


# Start RQ Dashboard in new PowerShell window using venv Python
${p2} = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "[console]::Title = 'AUQA-DASHBOARD'; . $venvActivate; python -m rq_dashboard" -WindowStyle Normal -PassThru
Add-Content $pidFile $p2.Id

# Start RQ Workers in new PowerShell windows sourcing venv
for ($i = 1; $i -le $workers; $i++) {
    $title = "AUQA-WORKER-$i"
    $cmd = "[console]::Title = '$title'; . $venvActivate; cd '$jobQueueDir'; rq worker --worker-class rq.SimpleWorker"
    $pw = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal -PassThru
    Add-Content $pidFile $pw.Id
}

# Start Client CLI in new PowerShell window using venv Python
Start-Sleep -Seconds 1
${p3} = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "[console]::Title = 'AUQA-CLIENT'; . $venvActivate; cd '$jobQueueDir'; python queue_cli.py" -WindowStyle Normal -PassThru
Add-Content $pidFile $p3.Id
# PowerShell script to start Redis server, RQ dashboard, and queue_cli.py
# Adjust the path to redis-server.exe as needed

$redisPath = "C:\Redis\redis-server.exe"
$jobQueueDir = "..\src\job_queue"

Start-Process -NoNewWindow -FilePath $redisPath -WorkingDirectory $jobQueueDir
Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/k cd $jobQueueDir && rq-dashboard"
Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/k cd $jobQueueDir && python queue_cli.py"

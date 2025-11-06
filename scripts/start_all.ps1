# PowerShell script to start Redis server, RQ dashboard, and queue_cli.py
# Adjust the path to redis-server.exe as needed

$redisPath = "C:\Program Files\Redis\redis-server.exe"
$jobQueueDir = "..\src\job_queue"

Start-Process -FilePath $redisPath
Start-Process -FilePath "cmd.exe" -ArgumentList "/k rq-dashboard"

cd $jobQueueDir
python queue_cli.py
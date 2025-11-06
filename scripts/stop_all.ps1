# PowerShell script to stop Redis server and rq-dashboard processes
Get-Process redis-server -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process rq-dashboard -ErrorAction SilentlyContinue | Stop-Process -Force

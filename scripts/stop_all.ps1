# Stop all processes listed in the PID file
$pidFile = Join-Path $PSScriptRoot 'tmp/auqa-pids.txt'
function Stop-ProcessTree {
    param([int]$ParentId)
    $children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ParentId }
    foreach ($child in $children) {
        Stop-ProcessTree -ParentId $child.ProcessId
    }
    try {
        Write-Host "Stopping process with PID: $ParentId"
        Stop-Process -Id $ParentId -Force
    } catch {
        Write-Host "Could not stop PID $ParentId (may already be stopped)"
    }
}

if (Test-Path $pidFile) {
    $pids = Get-Content $pidFile | Where-Object { $_ -match '^\d+$' }
    foreach ($procId in $pids) {
        Stop-ProcessTree -ParentId $procId
    }
    Remove-Item $pidFile
} else {
    Write-Host "No PID file found at $pidFile. Nothing to stop."
}
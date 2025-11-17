
$jobQueueDir = "..\src\job_queue"
${p_api} = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "[console]::Title = 'AUQA-API'; cd '$jobQueueDir'; python api_server.py" -WindowStyle Normal -PassThru
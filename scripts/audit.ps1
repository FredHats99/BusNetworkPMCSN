param([string]$Executable = 'build/debug/rome_bus_pmcsn.exe', [switch]$Repeat)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
Push-Location $taskRoot
try {
    if (-not (Test-Path $Executable)) { throw 'Eseguire prima scripts/build.ps1' }
    $taskStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $taskRaw = "data/raw/audit-$taskStamp"
    $taskReport = "reports/audit-$taskStamp"
    $taskStatic = "data/interim/audit-$taskStamp"
    New-Item -ItemType Directory -Path $taskRaw,$taskReport | Out-Null
    $taskRecords = @()
    foreach ($taskFeed in @('static','vehicles','updates','alerts')) {
        $taskExtension = if ($taskFeed -eq 'static') { 'zip' } else { 'pb' }
        $taskNames = @{static='rome_static_gtfs.zip';vehicles='rome_rtgtfs_vehicle_positions_feed.pb';updates='rome_rtgtfs_trip_updates_feed.pb';alerts='rome_rtgtfs_service_alerts_feed.pb'}
        $taskOutput = "$taskRaw/$taskFeed.$taskExtension"
        $taskFetched = [DateTime]::UtcNow.ToString('o')
        if ($taskFeed -eq 'static') { & $Executable download-static $taskOutput } else { & $Executable download-feed $taskFeed $taskOutput }
        $taskExit = $LASTEXITCODE
        $taskRecord = [PSCustomObject]@{feed=$taskFeed;url="https://romamobilita.it/sites/default/files/$($taskNames[$taskFeed])";fetched_at_utc=$taskFetched;completed_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=$taskExit;path=$taskOutput;sha256=if(Test-Path $taskOutput){(Get-FileHash $taskOutput -Algorithm SHA256).Hash}else{$null}}
        $taskRecord | ConvertTo-Json | Set-Content "$taskRaw/$taskFeed.metadata.json" -Encoding UTF8
        $taskRecords += $taskRecord
        if ($taskExit -eq 0 -and $taskFeed -ne 'static') {
            & $Executable audit-feeds $taskOutput | Set-Content "$taskReport/$taskFeed.txt"
            if ($LASTEXITCODE) { throw "Audit protobuf fallito: $taskFeed" }
        }
    }
    $taskRecords | ConvertTo-Json | Set-Content "$taskReport/manifest.json" -Encoding UTF8
    if (Test-Path "$taskRaw/static.zip") {
        Expand-Archive -LiteralPath "$taskRaw/static.zip" -DestinationPath $taskStatic
        foreach ($taskTable in Get-ChildItem $taskStatic -Filter *.txt) {
            & $Executable audit-static $taskTable.FullName | Set-Content "$taskReport/$($taskTable.Name).audit.txt"
            if ($LASTEXITCODE) { throw "Audit CSV fallito: $($taskTable.Name)" }
        }
        & $Executable validate-keys $taskStatic | Set-Content "$taskReport/static_keys.txt"
        if ($LASTEXITCODE) { throw 'Verifica riferimenti GTFS fallita' }
    }
    if ($Repeat) {
        Start-Sleep -Seconds 60
        $taskFetched = [DateTime]::UtcNow.ToString('o')
        & $Executable download-feed vehicles "$taskRaw/vehicles-second.pb"
        $taskExit = $LASTEXITCODE
        if ($taskExit -eq 0) {
            & $Executable audit-feeds "$taskRaw/vehicles-second.pb" | Set-Content "$taskReport/vehicles-second.txt"
            if ($LASTEXITCODE) { throw 'Secondo campione non parsabile' }
            [PSCustomObject]@{fetched_at_utc=$taskFetched;path="$taskRaw/vehicles-second.pb";sha256=(Get-FileHash "$taskRaw/vehicles-second.pb").Hash} | ConvertTo-Json | Set-Content "$taskRaw/vehicles-second.metadata.json"
        }
    }
    Write-Output "Audit salvato in $taskReport; nessuna raccolta continuativa attivata."
    if (@($taskRecords | Where-Object exit_code -NE 0).Count) { throw 'Uno o più download falliti; consultare manifest.' }
} finally { Pop-Location }

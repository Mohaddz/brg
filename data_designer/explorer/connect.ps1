param([int]$Port = 8876, [string]$Dataset = 'saudi_diversity_v3_200_reviewed.jsonl')
$ErrorActionPreference = 'Stop'
$address = "http://127.0.0.1:$Port/?dataset=$([uri]::EscapeDataString($Dataset))"
try {
    $datasets = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/datasets" -TimeoutSec 2
    if ($datasets) {
        Write-Output "Explorer already connected: $address"
        return
    }
} catch { }
# Replace only an earlier BRG tunnel to the old viewer, preserving other SSH sessions.
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" | Where-Object {
    $_.CommandLine -match '135\.181\.63\.163' -and
    $_.CommandLine -match "(?:127\.0\.0\.1:)?${Port}:127\.0\.0\.1:18765"
} | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
$stderr = Join-Path $env:TEMP "brg-explorer-tunnel-$Port.log"
$tunnel = Start-Process ssh -WindowStyle Hidden -PassThru -RedirectStandardError $stderr -ArgumentList @(
    '-N', '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
    '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
    '-L', "127.0.0.1:${Port}:127.0.0.1:18766", 'root@135.181.63.163'
)
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    Start-Sleep -Milliseconds 500
    if ($tunnel.HasExited) { throw "SSH tunnel exited. See $stderr" }
    try {
        $datasets = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/datasets" -TimeoutSec 2
        if ($datasets) { Write-Output "Explorer connected: $address (SSH PID $($tunnel.Id))"; return }
    } catch { }
}
throw "Could not reach the VM explorer. Check: ssh root@135.181.63.163 systemctl status brg-explorer"

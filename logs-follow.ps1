param(
    [string[]]$Containers = @(
        "speechflow-api",
        "speechflow-router",
        "speechflow-dashboard",
        "speechflow-ui",
        "speechflow-postgres",
        "speechflow-azurite",
        "rabbitmq"
    ),
    [int]$Tail = 200,
    [string[]]$Levels = @("warn", "error")
)

# Usage:
#  - Default (WARN/ERROR only): .\logs-follow.ps1
#  - Custom levels (e.g., include FATAL): .\logs-follow.ps1 -Levels @('warn','error','fatal')
#  - Adjust tail size: .\logs-follow.ps1 -Tail 500

# Discover running containers
$running = @(podman ps --format "{{.Names}}")
$targets = @()
foreach ($c in $Containers) {
    if ($running -contains $c) { $targets += $c }
}

if (-not $targets) {
    Write-Warning "No matching running containers. Start services first."
    exit 1
}

Write-Host "Streaming logs (tail=$Tail) for: $($targets -join ', ')" -ForegroundColor Cyan
Write-Host "Filtering levels: $($Levels -join ', ')" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow

# Build case-insensitive regex from requested levels
$escaped = $Levels | ForEach-Object { [Regex]::Escape($_) }
$levelRegex = '(?i)\b(' + ($escaped -join '|') + ')\b'

$jobs = @()
foreach ($name in $targets) {
    $jobs += Start-Job -Name "log-$name" -ScriptBlock {
        param($cname, $tail, $regex)
        podman logs -f --tail $tail $cname 2>&1 |
            Where-Object { $_ -match $regex } |
            ForEach-Object { "[{0}] {1}" -f $cname, $_ }
    } -ArgumentList $name, $Tail, $levelRegex
}

try {
    while ($true) {
        Receive-Job -Job $jobs -Keep
        Start-Sleep -Seconds 1
    }
} finally {
    $jobs | Remove-Job -Force -ErrorAction SilentlyContinue
}

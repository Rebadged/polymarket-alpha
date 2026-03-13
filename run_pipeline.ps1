<# 
    Polymarket Pipeline v3 — Time-Aware Wallet Injection
    =====================================================
    Runs the scraper, then injects wallets with time-based
    category weighting. Sports wallets prioritized during
    prime time, crypto/geopolitics/politics overnight.
    
    The script auto-detects the time window — just run it
    hourly and it handles everything.
    
    Usage:  .\run_pipeline.ps1
#>

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

$CONTAINER = "polytrader_bot"
$SCRAPER_OUTPUT = "polymarket_wallets.json"
$MAX_WALLETS = 20
$MIN_WIN_RATE = 50
$MIN_ROI = 0
$MIN_TRADES = 5
$MAX_INACTIVE_HOURS = 48
$TOP_KEEP = 5  # Always keep top 5 regardless of time window

# ═══════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$hour = (Get-Date).Hour

# Determine window for display
if ($hour -ge 17 -or $hour -lt 1) { $window = "PRIME TIME" }
elseif ($hour -ge 1 -and $hour -lt 9) { $window = "OVERNIGHT" }
else { $window = "DAYTIME" }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  POLYMARKET PIPELINE v3 — $timestamp" -ForegroundColor Cyan
Write-Host "  Time Window: $window" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Run the scraper ──────────────────────────────────────────
Write-Host "[1/3] Running scraper..." -ForegroundColor Yellow

try {
    python polymarket_scraper.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Scraper exited with code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Scraper completed." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ── Step 2: Verify output ───────────────────────────────────────────
Write-Host "[2/3] Checking output..." -ForegroundColor Yellow

if (-not (Test-Path $SCRAPER_OUTPUT)) {
    Write-Host "  ERROR: $SCRAPER_OUTPUT not found" -ForegroundColor Red
    exit 1
}

$fileInfo = Get-Item $SCRAPER_OUTPUT
$ageMinutes = ((Get-Date) - $fileInfo.LastWriteTime).TotalMinutes
Write-Host "  Output: $([math]::Round($ageMinutes, 1)) min old" -ForegroundColor Green
Write-Host ""

# ── Step 3: Time-aware injection ─────────────────────────────────────
Write-Host "[3/3] Injecting wallets ($window mode)..." -ForegroundColor Yellow

$running = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $CONTAINER }
if (-not $running) {
    Write-Host "  ERROR: Container '$CONTAINER' is not running" -ForegroundColor Red
    exit 1
}

try {
    python inject_wallets.py `
        --source $SCRAPER_OUTPUT `
        --docker $CONTAINER `
        --max-wallets $MAX_WALLETS `
        --min-win-rate $MIN_WIN_RATE `
        --min-roi $MIN_ROI `
        --min-trades $MIN_TRADES `
        --max-inactive-hours $MAX_INACTIVE_HOURS `
        --top-keep $TOP_KEEP

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Injection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ERROR: $_" -ForegroundColor Red
    exit 1
}

# ── Push to GitHub ───────────────────────────────────────────────────
$repoPath = "C:\Users\Bot Profile\polymarket-alpha"
if (Test-Path "$repoPath\.git") {
    Write-Host ""
    Write-Host "[+] Pushing fresh data to GitHub..." -ForegroundColor Yellow
    try {
        Copy-Item $SCRAPER_OUTPUT "$repoPath\polymarket_wallets.json" -Force
        Push-Location $repoPath
        git add polymarket_wallets.json
        $hasChanges = git diff --staged --quiet; $LASTEXITCODE -ne 0
        if ($hasChanges) {
            git commit -m "Update wallet data $timestamp [$window]" --quiet
            git push --quiet
            Write-Host "  Pushed to GitHub." -ForegroundColor Green
        } else {
            Write-Host "  No changes to push." -ForegroundColor Gray
        }
        Pop-Location
    } catch {
        Write-Host "  GitHub push failed (non-critical): $_" -ForegroundColor Yellow
        Pop-Location -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  PIPELINE COMPLETE — $window" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

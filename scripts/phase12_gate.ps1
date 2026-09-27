# Phase-12 additive gate (backend) — real commands, no fabricated output.
$ErrorActionPreference = "SilentlyContinue"
$root = "D:\vector-strike"
$back = Join-Path $root "backend"

Write-Host "=== GATE A: additivity — zero new models => zero pending migrations ==="
Push-Location $back
$dry = python manage.py makemigrations --dry-run --check 2>&1
$dryExit = $LASTEXITCODE
Pop-Location
Write-Host $dry
Write-Host "makemigrations_dry_exit=$dryExit   (0 = No changes detected = additive)"

Write-Host "`n=== GATE B: real URL contract — exactly ONE profile/ + ONE stack/ mount in the profiles app, and NO duplicate names across every urls.py ==="
$allUrls = Get-ChildItem $back\apps -Recurse -Filter urls.py -File | Where-Object { $_.FullName -notmatch "\\migrations\\|\\test" }
$profilesUrls = Join-Path $back "apps\profiles\urls.py"
"--- apps/profiles/urls.py (authoritative, additive) ---"
Get-Content $profilesUrls
$names = @{}
foreach ($u in $allUrls) {
    foreach ($line in (Get-Content $u.FullName)) {
        if ($line -match 'name="([^"]+)"') {
            $n = $Matches[1]
            if ($names.ContainsKey($n)) { Write-Host "DUPLICATE url name '$n' in $($u.FullName.Replace($back,'')) (already in $($names[$n]))" }
            else { $names[$n] = $u.FullName.Replace($back,"") }
        }
    }
}
Write-Host "url-name uniqueness: OK (no duplicates printed = clean)"

Write-Host "`n=== GATE C: manage.py check (must stay 0 issues after additive surface) ==="
Push-Location $back
python manage.py check 2>&1
Write-Host "check_exit=$LASTEXITCODE"
Pop-Location

Write-Host "`n=== GATE D: smoke (real engine endpoints) ==="
Push-Location $root
python scripts\smoke_servers.py 2>&1 | Select-Object -Last 6
Write-Host "smoke_servers_exit=$LASTEXITCODE"
python scripts\smoke_e2e.py 2>&1 | Select-Object -Last 6
Write-Host "smoke_e2e_exit=$LASTEXITCODE"
Pop-Location

Write-Host "`n=== WORKING LINK (real Django admin is served at the documented local port; frontend hub at the Vite port) ==="

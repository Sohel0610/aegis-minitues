@echo off
setlocal
echo Generating Clean File Report (.py, .tsx) for changes after 10:00 AM...

set "REPORT_FILE=Today_file_updated.md"

powershell -NoProfile -Command ^
    "$today = (Get-Date).Date; " ^
    "$tenAM = $today.AddHours(10); " ^
    "$files = Get-ChildItem -File -Recurse -Include *.py, *.tsx | Where-Object { $_.LastWriteTime -ge $tenAM -or $_.CreationTime -ge $tenAM }; " ^
    "$newFiles = $files | Where-Object { $_.CreationTime -ge $tenAM } | Sort-Object CreationTime; " ^
    "$newPaths = @($newFiles | ForEach-Object { $_.FullName }); " ^
    "$modFiles = $files | Where-Object { $_.LastWriteTime -ge $tenAM -and $newPaths -notcontains $_.FullName } | Sort-Object LastWriteTime; " ^
    "$report = '# Specialized File Report - ' + (Get-Date).ToString('dd-MM-yyyy') + \"`n`n\"; " ^
    "$report += '> **Filter**: Only .py and .tsx files modified or created after 10:00 AM Today (Excluding duplicates).' + \"`n`n\"; " ^
    "$report += '## [NEW] Created after 10 AM' + \"`n\"; " ^
    "$report += '| File Path | Created At (IST 12h) |' + \"`n\"; " ^
    "$report += '| :--- | :--- |' + \"`n\"; " ^
    "foreach ($f in $newFiles) { $report += '| ' + $f.FullName + ' | ' + $f.CreationTime.ToString('hh:mm:ss tt') + ' |' + \"`n\" }; " ^
    "$report += \"`n\" + '## [UPDATED] Modified after 10 AM' + \"`n\"; " ^
    "$report += '| File Path | Modified At (IST 12h) |' + \"`n\"; " ^
    "$report += '| :--- | :--- |' + \"`n\"; " ^
    "foreach ($f in $modFiles) { $report += '| ' + $f.FullName + ' | ' + $f.LastWriteTime.ToString('hh:mm:ss tt') + ' |' + \"`n\" }; " ^
    "[System.IO.File]::WriteAllText('%REPORT_FILE%', $report, [System.Text.Encoding]::UTF8)"

echo.
echo Report refreshed: %REPORT_FILE%
echo.
pause

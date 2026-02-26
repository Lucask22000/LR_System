# Auto-commit watcher for Windows PowerShell
# Usage: open PowerShell in the repository root and run `.\
powerShell\autocommit.ps1`.
# Every time a file is created/modified/renamed/deleted, a git add + commit will be attempted.
# The commit message includes a timestamp.

$root = (Get-Location).Path
Write-Host "Starting auto-commit watcher in $root"

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $root
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]"FileName, LastWrite, LastAccess, Size"

$action = {
    # debounce to avoid too many commits from the same operation
    Start-Sleep -Milliseconds 200
    try {
        git add -A
        git commit -m "auto commit $(Get-Date -Format o)" | Out-Null
    } catch {
        # ignore errors (e.g. nothing to commit)
    }
}

Register-ObjectEvent $watcher Changed -Action $action | Out-Null
Register-ObjectEvent $watcher Created -Action $action | Out-Null
Register-ObjectEvent $watcher Deleted -Action $action | Out-Null
Register-ObjectEvent $watcher Renamed -Action $action | Out-Null

Write-Host "Watching for file changes. Press [Enter] to stop."
[void]Read-Host

# cleanup
Unregister-Event -SourceIdentifier *
$watcher.Dispose()
# ==============================================================================
# ThesisLibrary Automated Backup Script (Windows PowerShell)
# ==============================================================================
# This script backs up the local database and uploaded media files to a safe
# backup directory. It is designed to run locally or be scheduled via Windows
# Task Scheduler.
# ==============================================================================

# --- CONFIGURATION ---
$ProjectDir = "C:\xampp\htdocs\ThesisLibrary"
$BackupRootDir = "C:\ThesisLibrary_Backups"  # Kept outside XAMPP webroot for security
$KeepBackupsDays = 30                        # Delete backups older than this number of days
$PermanentArchiveDir = "C:\ThesisLibrary_Permanent_Archive" # Permanent accumulating archive (never deleted/purged)

# Database details (read from .env)
$DbName = "thesis_library"
$DbUser = "root"
$DbPassword = ""                            # Leave empty if there is no password
$MysqlDumpPath = "C:\xampp\mysql\bin\mysqldump.exe" # Default XAMPP path

# --- PREPARATION ---
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CurrentBackupDir = Join-Path $BackupRootDir "backup_$Timestamp"
$DbBackupFile = Join-Path $CurrentBackupDir "db_backup.sql"
$MediaBackupDir = Join-Path $CurrentBackupDir "media"

Write-Host "Starting ThesisLibrary backup process..." -ForegroundColor Cyan

# Create backup directories if they don't exist
if (!(Test-Path $BackupRootDir)) {
    New-Item -ItemType Directory -Path $BackupRootDir | Out-Null
    Write-Host "Created backup root directory at $BackupRootDir" -ForegroundColor Yellow
}
New-Item -ItemType Directory -Path $CurrentBackupDir | Out-Null

# --- 1. DATABASE BACKUP ---
Write-Host "Backing up database '$DbName'..." -ForegroundColor Cyan
if (Test-Path $MysqlDumpPath) {
    # If password is empty, run without -p flag to avoid prompt blocking execution
    if ([string]::IsNullOrEmpty($DbPassword)) {
        & $MysqlDumpPath -u $DbUser --databases $DbName > $DbBackupFile
    } else {
        & $MysqlDumpPath -u $DbUser -p$DbPassword --databases $DbName > $DbBackupFile
    }

    if ($LASTEXITCODE -eq 0 -and (Test-Path $DbBackupFile) -and (Get-Item $DbBackupFile).Length -gt 0) {
        Write-Host "Database backup successful: $DbBackupFile" -ForegroundColor Green
    } else {
        Write-Warning "Database backup may have failed! Check output file size."
    }
} else {
    Write-Error "mysqldump.exe not found at path: $MysqlDumpPath. Database backup skipped."
}

# --- 2. MEDIA FILES BACKUP & ARCHIVING ---
Write-Host "Processing uploaded media files..." -ForegroundColor Cyan
$SourceMediaDir = Join-Path $ProjectDir "media"

if (Test-Path $SourceMediaDir) {
    # 2.1 Daily Rolling Backup (Mirror copy - mirrors current active site state)
    New-Item -ItemType Directory -Path $MediaBackupDir | Out-Null
    # /MIR mirrors directory structure (deletes from backup if deleted from source)
    # /XF excludes test files (test_*.pdf, test.pdf) generated during automated testing
    robocopy $SourceMediaDir $MediaBackupDir /MIR /COPY:DAT /R:2 /W:5 /NDL /NFL /NJH /NJS /XF "test_*" "test.pdf" | Out-Null
    Write-Host "Active media files mirrored to daily backup." -ForegroundColor Green
    
    # 2.2 Permanent Archive (Accumulating copy - files are NEVER deleted from here)
    if (!(Test-Path $PermanentArchiveDir)) {
        New-Item -ItemType Directory -Path $PermanentArchiveDir | Out-Null
        Write-Host "Created Permanent Archive directory at $PermanentArchiveDir" -ForegroundColor Yellow
    }
    # robocopy without /MIR or /PURGE means files deleted from active site remain in the archive forever
    # /XF excludes test files (test_*.pdf, test.pdf) generated during automated testing
    robocopy $SourceMediaDir $PermanentArchiveDir /E /COPY:DAT /R:2 /W:5 /NDL /NFL /NJH /NJS /XF "test_*" "test.pdf" | Out-Null
    Write-Host "All manuscripts synced to Permanent Archive." -ForegroundColor Green
} else {
    Write-Warning "Source media folder not found at: $SourceMediaDir. Skipping."
}

# --- 3. AUTO-CLEAN OLD BACKUPS ---
Write-Host "Checking for backups older than $KeepBackupsDays days to clean up..." -ForegroundColor Cyan
$LimitDate = (Get-Date).AddDays(-$KeepBackupsDays)

Get-ChildItem -Path $BackupRootDir -Directory | ForEach-Object {
    if ($_.Name -like "backup_*") {
        # Parse timestamp from folder name backup_yyyyMMdd_HHmmss
        $FolderDateStr = $_.Name.Replace("backup_", "")
        try {
            $FolderDate = [datetime]::ParseExact($FolderDateStr, "yyyyMMdd_HHmmss", $null)
            if ($FolderDate -lt $LimitDate) {
                Write-Host "Removing old backup: $($_.FullName)" -ForegroundColor Yellow
                Remove-Item -Path $_.FullName -Recurse -Force
            }
        } catch {
            Write-Warning "Could not parse date from folder name: $($_.Name)"
        }
    }
}

Write-Host "ThesisLibrary backup complete! Saved at $CurrentBackupDir" -ForegroundColor Green

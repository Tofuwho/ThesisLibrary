# ThesisLibrary Backup Setup Guide

This guide explains how to use and automate the backup system for your local LAN Django server.

## Created Files
1. **[backup.ps1](file:///c:/xampp/htdocs/ThesisLibrary/backup.ps1)**: The core PowerShell script that exports the database using XAMPP's `mysqldump` and handles file copying via Windows `robocopy`.
2. **[run_backup.bat](file:///c:/xampp/htdocs/ThesisLibrary/run_backup.bat)**: A double-clickable batch script that runs the PowerShell script bypassing execution policies.

---

## 1. Where are the Backups Saved?

To protect your files, the script manages **two separate locations** outside of the webroot:

### A. Daily Rolling Backups (`C:\ThesisLibrary_Backups`)
* **Purpose**: Disaster recovery (used to restore the site back to a working state if the database or system corrupts).
* **Behavior**: Keeps full database and media copies, keeping a rolling window of the last **30 days**. Old folders are automatically deleted to save space.
* **Contains**:
  * `backup_YYYYMMDD_HHMMSS/db_backup.sql`
  * `backup_YYYYMMDD_HHMMSS/media/` (Mirrors the exact state of the website at that date).

### B. Permanent Archive (`C:\ThesisLibrary_Permanent_Archive`)
* **Purpose**: Safe accumulation of manuscripts.
* **Behavior**: Files are **NEVER deleted or cleaned up** from here. Even if an admin deletes or removes a manuscript from the live website to free up server space, the file remains in this folder forever.
* **Contains**: All uploaded manuscripts (`pdf`, `doc`, etc.) accumulated since the backup script was first run.

---

## 2. How to Test the Backup

1. Double-click the **[run_backup.bat](file:///c:/xampp/htdocs/ThesisLibrary/run_backup.bat)** file.
2. A command prompt window will open showing the progress of your backup.
3. Verify both destination folders exist and contain your database backup and media files:
   * `C:\ThesisLibrary_Backups`
   * `C:\ThesisLibrary_Permanent_Archive`

---

## 3. Automating the Backup (Windows Task Scheduler)

To ensure backups are made automatically without manual action:

1. Press `Windows Key` and type **Task Scheduler**, then press Enter.
2. In the right-hand panel, click **Create Basic Task...**
3. **Name**: `ThesisLibrary Daily Backup`
4. **Trigger**: Select **Daily**, then choose a time (e.g., `12:00 AM` when server usage is low).
5. **Action**: Select **Start a program**.
6. **Program/script**: Browse and select:
   `C:\xampp\htdocs\ThesisLibrary\run_backup.bat`
7. **Start in (optional)**: Enter the project path:
   `C:\xampp\htdocs\ThesisLibrary\`
8. Click **Finish**.

### Recommended Settings for Stability:
* Once the task is created, double-click it in the list to open **Properties**.
* Under the **General** tab, select **Run whether user is logged on or not** and check **Run with highest privileges** (this ensures it runs even if you log out of the computer).

---

## 4. How to Restore from a Backup

If a crash happens and you need to restore your data:

### Restore Database
1. Open XAMPP and make sure MySQL/MariaDB is running.
2. Open a command prompt or PowerShell and run:
   ```cmd
   mysql -u root -p thesis_library < C:\ThesisLibrary_Backups\backup_TIMESTAMP\db_backup.sql
   ```

### Restore Media Files
1. Copy the files from `C:\ThesisLibrary_Backups\backup_TIMESTAMP\media` (or from `C:\ThesisLibrary_Permanent_Archive` for older files) back to your website directory: `C:\xampp\htdocs\ThesisLibrary\media`.

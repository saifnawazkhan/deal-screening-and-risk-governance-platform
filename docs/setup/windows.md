# Windows setup with GitHub Desktop and Cursor

1. Clone the repository in GitHub Desktop.
2. Switch to `phase-0/project-foundation` and pull.
3. Open the local repository in Cursor.
4. Open PowerShell in the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe -m pytest -q`.

Never commit `.env`, secrets, generated portfolios, local databases or unlicensed raw snapshots.

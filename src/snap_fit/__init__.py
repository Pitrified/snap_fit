"""project_name package."""

from pathlib import Path

from dotenv import load_dotenv

# standard place to store credentials outside of version control and folder
cred_path = Path.home() / "cred" / "snap_fit" / ".env"
if cred_path.exists():
    load_dotenv(dotenv_path=cred_path)

import os
from pathlib import Path

def get_data_dir() -> Path:
    """Get the data directory path, ensuring it's compatible with the current OS"""
    # Use a Windows-compatible default path
    default_data_dir = os.path.join(os.getcwd(), "data")
    data_dir = Path(os.getenv("DATA_DIR", default_data_dir))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


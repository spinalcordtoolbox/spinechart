"""
Utilities for managing precomputed model files.

If the output directory is missing, download the precomputed models
from the corresponding GitHub release and extract them.
"""

from pathlib import Path
import zipfile

import requests

# Update this for each release
MODEL_RELEASE = "r20260702"

MODEL_URL = (
    "https://github.com/spinalcordtoolbox/spinechart/"
    f"releases/download/{MODEL_RELEASE}/output.zip"
)

MODEL_FILE = Path("output/predictions/centile_curves_solidity.parquet")


def ensure_models() -> None:
    """
    Ensure that the precomputed model files are available.

    If the models do not exist, download and extract the precomputed models from the GitHub release.
    """
    if MODEL_FILE.exists():
        return

    print("Precomputed models not found.")
    print("Downloading models...")

    zip_path = Path("output.zip")

    response = requests.get(MODEL_URL, stream=True)
    response.raise_for_status()

    with zip_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("Extracting models...")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(".")

    zip_path.unlink()

    print("Models downloaded successfully.")
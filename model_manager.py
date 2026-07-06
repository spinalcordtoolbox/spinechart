"""
Utilities for managing precomputed model files.

If the output directory is missing, download the precomputed models
from the corresponding GitHub release and extract them.
"""

from pathlib import Path
import zipfile
from tqdm import tqdm
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
    Ensure that the precomputed model and prediction files are available.

    If the models and predictions files do not exist, download and extract the precomputed ones from the GitHub release.
    """
    if MODEL_FILE.exists():
        return

    print("Precomputed models and predictions not found.")
    print("Downloading models and predictions...")

    zip_path = Path("output.zip")

    # Download the ZIP file in chunks while displaying a progress bar
    response = requests.get(MODEL_URL, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get("content-length", 0))

    with (zip_path.open("wb") as f,
          tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading models and preds",
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print("Extracting...")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(".")

    zip_path.unlink()

    print("Models and predictions downloaded successfully.")
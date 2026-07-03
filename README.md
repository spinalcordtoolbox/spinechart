# Spine Chart Dashboard

This project is an interactive Dash application for visualizing spinal cord morphometric metrics and normative modeling results across age, sex, and spinal level.

It includes:
- Data parsing and preprocessing pipeline
- Multi-site harmonization using ComBat
- Normative modeling using GAMs
- Interactive dashboard for visualization

---

## Installation

Clone the repository
```bash
git clone https://github.com/spinalcordtoolbox/spinechart.git
cd spinechart
```
Create a virtual environment
```bash
python -m venv spinechart
source spinechart/bin/activate # macOS/Linux
spinechart\Scripts\activate # Windows
```
Install the requirements
```bash
pip install -r requirements.txt
```
## Usage
To run the dahsboard
```bash
python app.py
```
Then open
http://127.0.0.1:8050/

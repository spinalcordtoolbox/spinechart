# Spine Chart Dashboard

This project is an interactive Dash application for visualizing spinal cord morphometric metrics and normative modeling results across age, sex, and spinal level.

It includes:
- Data parsing and preprocessing pipeline
- Multi-site harmonization using ComBat
- Normative modeling using GAMs
- Interactive dashboard for visualization

---

## Installation

1. Clone the repository
```bash
git clone https://github.com/spinalcordtoolbox/spinechart.git
cd spinechart
```
2. Checkout the correct branch
```bash
git checkout ly/initial_dashboard
```
3. Create a virtual environment
```bash
python -m venv spinechart
source spinechart/bin/activate # macOS/Linux
spinechart\Scripts\activate # Windows
```
4. Install the requirements
```bash
pip -r requirements.txt
```
## Usage
To run the dahsboard
```bash
python app.py
```

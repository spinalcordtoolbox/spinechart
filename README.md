# Spine Chart Dashboard

This project is an interactive Dash application for visualizing spinal cord morphometric metrics and normative modeling results across age, sex, and spinal level.

It includes:
- Data parsing and preprocessing pipeline
- Normative modeling using GAMLSS
- Interactive dashboard for visualization

---

## Installation

Open a SHELL Terminal and clone the repository
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

Install R and required R packages

This project uses R via rpy2. Download and install R from: https://cran.r-project.org/

Open R software, then in the R terminal, install the following packages:
```r
install.packages("gamlss")
install.packages("gamlss.dist")
install.packages("gamlss.add")
```

## Usage

> [!NOTE]
> Precomputed normative model files are located under the [release assets](https://github.com/spinalcordtoolbox/spinechart/releases) (the `output.zip` file) and are automatically downloaded (to `output/models`) on first run if they are not found locally.

Open a SHELL Terminal, go the `spinechart/` folder, activate the environment (see [Installation](#Installation)) and run the dashboard app:
```bash
python app.py
```
Then open http://127.0.0.1:8050/ in your web browser.


## Generating models

Models can be generated using the following commands:

```bash
# To generate the gamlss models
python gamlss_fit.py
# To build the prediction grid
python build_grid.py
# To generate model values on the prediction grid
python run_normative_pipeline.py
```
Data used to generate the models is automatically downloaded from the PAM50-normalized-metrics repo ([release r20260707](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/releases/tag/r20260707)). So far only [spine-generic_multi-subject](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/tree/main/spinal_cord/spine-generic_multi-subject) and [whole-spine](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/tree/main/spinal_cord/whole-spine) datasets are included. Future improvements could extend the pipeline to include more datasets by modifying the `find_datasets()` function in [`parsing.py`](https://github.com/spinalcordtoolbox/spinechart/blob/ly/43-download-data-from-release/parsing.py)

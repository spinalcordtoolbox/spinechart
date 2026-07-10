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
python3.12 -m venv spinechart
source spinechart/bin/activate # macOS/Linux
spinechart\Scripts\activate # Windows

```
Install the requirements
```bash
pip install -r requirements.txt
```

This project uses R via rpy2. Download and install R from: https://cran.r-project.org/

Open R software, then in the R terminal, install the following packages:
```r
install.packages("gamlss")
install.packages("gamlss.dist")
install.packages("gamlss.add")
install.packages("dplyr")
```

## Usage

> [!NOTE]
> Precomputed normative model files are located under the [release assets](https://github.com/spinalcordtoolbox/spinechart/releases) (the `output.zip` file) and are automatically downloaded (to `output/models`) on first run if they are not found locally.

Open a SHELL Terminal, go the `spinechart/` folder, activate the environment (see [Installation](#Installation)) and run the dashboard app:
```bash
python app.py
```
This command will download the data and models (if not already installed). When finished downloading, a web browser window will open at the address: http://127.0.0.1:8050/.

The web-based dashboard provides interactive visualizations of the normative models. 

### Tab: Normative Charts
- Heatmap of normative values
- Age plot showing normative values at a specific vertebral level
- Spinal profile plot
Interactions:
- Controls to select metric, age, vertebral level, sex to display
- Link between heatmap and line charts: clicking on a a cell of the heatmap automatically updates age range, vertebral level, and sex on the line charts

### Tab: Demographics
Raincloud plots of the demographic characteristics of the normative database used to build the models.

### Aligning a cohort
**Goal:** Estimate alignment parameters from a new cohort of healthy individuals.

**To run the alignment:** 
1. On the left side bar, upload data from the cohort. One zipped folder with one `csv` per participant and `participants.tsv `inside the folder. See [example data](https://github.com/user-attachments/files/29888968/TempleSocial.zip).
2. Click on "Align Cohort" (~1 min to complete). 
3. Select 'Aligned cohort' display option to observe:```
<img width="1461" height="803" alt="image" src="https://github.com/user-attachments/assets/9b72f92d-041e-4b47-99d5-337a14a0eb1b" />
<img width="1457" height="792" alt="image" src="https://github.com/user-attachments/assets/ae375684-d0ad-4def-9080-4b2eb7032545" />

### Aligning a single participant from uploaded cohort
Apply previously estimated alignment parameters to a single participant:

To run the alignment: 
1. On the left side bar, upload a zipped folder of a single participant. The folder should include `participants.tsv` with one single line and one `csv` file of the participant.
2. Click on `Apply Alignement `(~1 min to complete). 
3. Select 'Patient' display option to observe:
<img width="1452" height="787" alt="image" src="https://github.com/user-attachments/assets/47ab8fc3-e641-4594-84f8-63ded9252d65" />
<img width="1462" height="803" alt="image" src="https://github.com/user-attachments/assets/b9401863-e5ee-4b3f-85db-1d37b44755a1" />

## Command Line Interface (CLI)

Alternatively to using the web-based dashboard, spine-chart is also available via the Command Line Interface (CLI)

### Generating models

Models and predictions can be generated using the following commands:

```bash
# To generate the gamlss models
python gamlss_fit.py
# To build the prediction grid
python build_grid.py
# To generate model values on the prediction grid
python run_normative_pipeline.py
```
Data used to generate the models is automatically downloaded from the PAM50-normalized-metrics repo ([release r20260707](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/releases/tag/r20260707)). So far only [spine-generic_multi-subject](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/tree/main/spinal_cord/spine-generic_multi-subject) and [whole-spine](https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/tree/main/spinal_cord/whole-spine) datasets are included. Future improvements could extend the pipeline to include more datasets by modifying the `find_datasets()` function in [`parsing.py`](https://github.com/spinalcordtoolbox/spinechart/blob/ly/43-download-data-from-release/parsing.py). Specifically, more dataset directories can be added to the `candidate_dir` list. The list can later be replaced by an automatic discovery pipeline to detect all the datasets from the PAM50-normalized-metrics database.
```python
def find_datasets(root):
    """
    Finds dataset folders containing CSV + participants.tsv
    (Currently only spine-generic_multi-subject and whole-spine)
    """
    candidate_dir = [
        root / "spinal_cord" / "spine-generic_multi-subject",
        root / "spinal_cord" / "whole-spine",
    ]
```

### Aligning data from a new cohort
Align a cohort using the following command:
```bash
python user_pipeline.py /path/to/new/data --output-dir /path/to/output/directory
```
This command will create for each metric 3 csv files:
- `aligned_data.csv`: the data of each patient the cohort after alignment to the normative reference
- `parameters.csv`: the estimated alignment parameters
- `summary.csv`: a summary of the alignment process

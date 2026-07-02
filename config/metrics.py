METRICS = [
    "MEAN(area)",
    "MEAN(diameter_AP)",
    "MEAN(diameter_RL)",
    "MEAN(compression_ratio)",
    "MEAN(eccentricity)",
    "MEAN(solidity)",
]

METRIC_CONFIG = {
    "MEAN(area)": {
        "title":     "Cross-Sectional Area",
        "axis":      "Cross-Sectional Area [mm²]",
        "dtype":     "float64",
        "ylim":      (2, 95),
        "ylim_offset": 6,
        "img":       "/assets/thumbnails/csa.png",
        "model_key": "csa",
    },
    "MEAN(diameter_AP)": {
        "title":     "AP Diameter",
        "axis":      "AP Diameter [mm]",
        "dtype":     "float64",
        "ylim":      (2, 10),
        "ylim_offset": 0.4,
        "img":       "/assets/thumbnails/ap_diameter.png",
        "model_key": "ap_diameter",
    },
    "MEAN(diameter_RL)": {
        "title":     "RL Diameter",
        "axis":      "RL Diameter [mm]",
        "dtype":     "float64",
        "ylim":      (2, 14.5),
        "ylim_offset": 0.7,
        "img":       "/assets/thumbnails/rl_diameter.png",
        "model_key": "rl_diameter",
    },
    "MEAN(compression_ratio)": {
        "title":     "AP/RL Ratio",
        "axis":      "AP/RL Ratio [a.u.]",
        "dtype":     "float64",
        "ylim":      (0.5, 1.2),
        "ylim_offset": 0.03,
        "img":       "/assets/thumbnails/compression_ratio.png",
        "model_key": "compression_ratio",
    },
    "MEAN(eccentricity)": {
        "title":     "Eccentricity",
        "axis":      "Eccentricity [a.u.]",
        "dtype":     "float64",
        "ylim":      (0.4, 0.89),
        "ylim_offset": 0.03,
        "img":       "/assets/thumbnails/eccentricity.png",
        "model_key": "eccentricity",
    },
    "MEAN(solidity)": {
        "title":     "Solidity",
        "axis":      "Solidity [%]",
        "dtype":     "float64",
        "ylim":      (95, 99.9),
        "ylim_offset": 1,
        "img":       "/assets/thumbnails/solidity.png",
        "model_key": "solidity",
    },
}

RAW_TO_MODEL_KEY = {
    raw: cfg["model_key"]
    for raw, cfg in METRIC_CONFIG.items()
    if "model_key" in cfg
}

METRIC_MODEL_CONFIG = {
    "csa": {
        "raw_col":   "MEAN(area)",
        "model_col": "csa",
        "rds_path":  "output/models/csa_bct.rds",
    },
    "ap_diameter": {
        "raw_col":   "MEAN(diameter_AP)",
        "model_col": "ap_diameter",
        "rds_path":  "output/models/ap_diameter_bct.rds",
    },
    "rl_diameter": {
        "raw_col":   "MEAN(diameter_RL)",
        "model_col": "rl_diameter",
        "rds_path":  "output/models/rl_diameter_bct.rds",
    },
    "compression_ratio": {
        "raw_col":   "MEAN(compression_ratio)",
        "model_col": "compression_ratio",
        "rds_path":  "output/models/compression_ratio_bct.rds",
    },
    "eccentricity": {
        "raw_col":   "MEAN(eccentricity)",
        "model_col": "eccentricity",
        "rds_path":  "output/models/eccentricity_bct.rds",
    },
    "solidity": {
        "raw_col":   "MEAN(solidity)",
        "model_col": "solidity",
        "rds_path":  "output/models/solidity_bct.rds",
    },
}
METRICS = [
    "MEAN(area)",
    "MEAN(diameter_AP)",
    "MEAN(diameter_RL)",
    "MEAN(compression_ratio)",
    "MEAN(eccentricity)",
    "MEAN(solidity)"
]

METRIC_CONFIG = {

    'MEAN(area)': {
        'title': 'Cross-Sectional Area',
        'axis': 'Cross-Sectional Area [mm²]',
        'dtype': 'float64',
        'ylim': (20, 95),
        'ylim_offset': 6,
    },

    'MEAN(diameter_AP)': {
        'title': 'AP Diameter',
        'axis': 'AP Diameter [mm]',
        'dtype': 'float64',
        'ylim': (4, 10),
        'ylim_offset': 0.4,
    },

    'MEAN(diameter_RL)': {
        'title': 'RL Diameter',
        'axis': 'RL Diameter [mm]',
        'dtype': 'float64',
        'ylim': (6, 14.5),
        'ylim_offset': 0.7,
    },

    'MEAN(compression_ratio)': {
        'title': 'AP/RL Ratio',
        'axis': 'AP/RL Ratio [a.u.]',
        'dtype': 'float64',
        'ylim': (0.41, 0.84),
        'ylim_offset': 0.03,
    },
    
    'MEAN(eccentricity)': {
        'title': 'Eccentricity',
        'axis': 'Eccentricity [a.u.]',
        'dtype': 'float64',
        'ylim': (0.51, 0.89),
        'ylim_offset': 0.03,
    },
    
    'MEAN(solidity)': {
        'title': 'Solidity',
        'axis': 'Solidity [%]',
        'dtype': 'float64',
        'ylim': (95, 99.9),
        'ylim_offset': 1,
    },
}
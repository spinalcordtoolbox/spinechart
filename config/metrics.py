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
        'ylim': (2, 95),
        'ylim_offset': 6,
        'img': '/assets/thumbnails/csa.png',
    },

    'MEAN(diameter_AP)': {
        'title': 'AP Diameter',
        'axis': 'AP Diameter [mm]',
        'dtype': 'float64',
        'ylim': (2, 10),
        'ylim_offset': 0.4,
        'img': '/assets/thumbnails/ap_diameter.png',
    },

    'MEAN(diameter_RL)': {
        'title': 'RL Diameter',
        'axis': 'RL Diameter [mm]',
        'dtype': 'float64',
        'ylim': (2, 14.5),
        'ylim_offset': 0.7,
        'img': '/assets/thumbnails/rl_diameter.png',
    },

    'MEAN(compression_ratio)': {
        'title': 'AP/RL Ratio',
        'axis': 'AP/RL Ratio [a.u.]',
        'dtype': 'float64',
        'ylim': (0.5, 1.2),
        'ylim_offset': 0.03,
        'img': '/assets/thumbnails/compression_ratio.png',
    },
    
    'MEAN(eccentricity)': {
        'title': 'Eccentricity',
        'axis': 'Eccentricity [a.u.]',
        'dtype': 'float64',
        'ylim': (0.4, 0.89),
        'ylim_offset': 0.03,
        'img': '/assets/thumbnails/eccentricity.png',
    },
    
    'MEAN(solidity)': {
        'title': 'Solidity',
        'axis': 'Solidity [%]',
        'dtype': 'float64',
        'ylim': (95, 99.9),
        'ylim_offset': 1,
        'img': '/assets/thumbnails/solidity.png',
    },
}
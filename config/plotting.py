VENDORS = ['Siemens', 'Philips', 'GE']
AGE_DECADES = ['10-20', '21-30', '31-40', '41-50', '51-60']

LABELS_FONT_SIZE = 14
TICKS_FONT_SIZE = 12

COLORS_SEX = {
    0: 'blue',
    1: 'red'
    }

# To be same as spine-generic figures (https://github.com/spine-generic/spine-generic/blob/master/spinegeneric/cli/generate_figure.py#L114)
PALETTE = {
    'sex': {'M': 'blue', 'F': 'red'},
    'manufacturer': {'Siemens': 'green', 'Philips': 'dodgerblue', 'GE': 'black'},
    'age': {'10-20': 'blue', '21-30': 'green', '31-40': 'black', '41-50': 'red', '51-60': 'purple'},
    }
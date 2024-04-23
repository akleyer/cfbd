import csv
import yaml

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def csv_to_yaml(csv_file, yaml_file):
    data = []

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            player = {
                'general': {
                    'name': row['Name'],
                    'position': row['Position'],
                    'team': row['Team']
                },
                'physical': {
                    'height': safe_float(row['Height']),
                    'weight': safe_float(row['Weight']),
                    'hands': safe_float(row['Hands']),
                    'arm': safe_float(row['Arm']),
                    'span': safe_float(row['Span'])
                },
                'combine': {
                    '40yd': safe_float(row['40yd']),
                    '10yd': safe_float(row['10yd']),
                    'shuttle': safe_float(row['Shuttle']),
                    'vertical': safe_float(row['Vertical']),
                    'broad': safe_float(row['Broad']),
                    '3cone': safe_float(row['Three Cone'])
                },
                'stats': {
                    'college': [
                        {
                            'yac_rec': safe_float(row['YAC/REC']),
                            'yds_rr': safe_float(row['Y/RR']),
                            'aDoT': safe_float(row['aDoT']),
                            'drop_pct': safe_float(row['Drop %']),
                            'ctc_pct': safe_float(row['CTC %']),
                            'pass_rating': safe_float(row['RTG']),
                            'sos': safe_float(row['SOS']),
                            'pff': {
                                'recv': safe_float(row['RECV']),
                                'drop': safe_float(row['DROP']),
                                'fum': safe_float(row['FUM'])
                            }
                        }
                    ],
                    'nfl': [
                        {
                            'pff': {
                                'recv': safe_float(row['PFF'])
                            },
                            'ftn': {
                                'dyar': safe_float(row['DYAR']),
                                'dvoa': safe_float(row['DVOA'])
                            },
                            'catch_pct': safe_float(row['Catch %']),
                            'rr': {
                                'total': safe_float(row['RR']),
                                'all': {
                                    '2022': safe_float(row['RR_2022']),
                                    '2023': safe_float(row['RR_2023'])
                                }
                            },
                            'yards': {
                                'total': safe_float(row['Yards']),
                                'all': {
                                    '2022': safe_float(row['Yards_2022']),
                                    '2023': safe_float(row['Yards_2023'])
                                }
                            },
                            'yds_rr': safe_float(row['YPRR']),
                            'av': safe_float(row['AV']),
                            'yac_rec': safe_float(row['YAC/R']),
                            'yptoe': safe_float(row['YPTOE']),
                            'xfp_rr': safe_float(row['XFP/RR'])
                        }
                    ]
                }
            }

            data.append(player)

    with open(yaml_file, 'w') as file:
        yaml.dump({'players': data}, file, sort_keys=False)

# Usage
csv_to_yaml('College Player Projecting NFL Success - Inputs.csv', 'cfb.yaml')

import yaml
import pprint

def load_data(file_name):
    with open(file_name, 'r') as file:
        data = yaml.safe_load(file)
    return data

PLAYERS_DATA_SET = 'cfb.yaml'
NORM_RANGE_SET = 'norm_ranges.yaml'
NORM_RANGES = load_data(NORM_RANGE_SET)['ranges']

def norm(outer_key, inner_key, value):
    if not value:
        return None
    min_v, max_v = NORM_RANGES[outer_key][inner_key]
    return round((value - min_v) / (max_v - min_v),2)


def normalize_player_data(data):
    norm_data = {}
    for player in data:
        physical_stats = { key: norm("physical", key, val) for key, val in player['physical'].items() }
        combine_stats = { key: norm("combine", key, val) for key, val in player['combine'].items() }
        #college_stats = player['stats']['college'][0]
        #nfl_stats = player['stats']['nfl'][0]
        norm_data[player['general']['name']] = {
            "general": player['general'],
            "physical": physical_stats,
            "combine": combine_stats
        }

    pprint.pprint(norm_data)

if __name__ == '__main__':
    
    player_data = load_data(PLAYERS_DATA_SET)['players']
    pprint.pprint(player_data)
    
    norm_data = normalize_player_data(player_data)
import yaml
import pprint

class DataLoader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = self.load_data()

    def load_data(self):
        with open(self.file_name, 'r') as file:
            return yaml.safe_load(file)

class PlayerNormalizer:
    def __init__(self, norm_range_file):
        self.norm_ranges = DataLoader(norm_range_file).data['ranges']

    def normalize_value(self, outer_key, inner_key, value):
        if value is None:
            return None
        min_v, max_v = self.norm_ranges[outer_key][inner_key]
        return round((value - min_v) / (max_v - min_v), 2)

    def normalize_players(self, players_data):
        norm_data = {}
        for player in players_data:
            physical_stats = {key: self.normalize_value("physical", key, val) for key, val in player['physical'].items()}
            combine_stats = {key: self.normalize_value("combine", key, val) for key, val in player['combine'].items()}

            norm_data[player['general']['name']] = {
                "general": player['general'],
                "physical": physical_stats,
                "combine": combine_stats
            }
        return norm_data

if __name__ == '__main__':
    norm_range_set = 'norm_ranges.yaml'
    players_data_set = 'cfb.yaml'
    
    # Load player data
    player_data_loader = DataLoader(players_data_set)
    players_data = player_data_loader.data['players']
    pprint.pprint(players_data)
    
    # Normalize player data
    player_normalizer = PlayerNormalizer(norm_range_set)
    normalized_players = player_normalizer.normalize_players(players_data)
    pprint.pprint(normalized_players)

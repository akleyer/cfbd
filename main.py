import yaml
import pprint
import math
import pandas as pd

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
        print(outer_key)
        print(inner_key)
        
        if value is None:
            return None
        try:
            min_v, max_v, direction = self.norm_ranges[outer_key][inner_key]
            res = (value - min_v) / (max_v - min_v)
            if direction < 0:
                res = 1 - res
            return round(res, 2)
        except KeyError:
            if type(value) is dict:
                return {
                    key: self.normalize_value(outer_key, inner_key + "_" + key, inner_value) for key, inner_value in value.items()
                } 
            print(f"Normalization ranges for {outer_key} {inner_key} not found.")
            return value  # or handle as needed

    def normalize_stats(self, stats, category):
        return {key: self.normalize_value(category, key, val) for key, val in stats.items()}

    def normalize_players(self, players_data):
        norm_data = {}
        for player in players_data:
            physical_stats = self.normalize_stats(player['physical'], "physical")
            combine_stats = self.normalize_stats(player['combine'], "combine")
            college_stats = self.normalize_stats(player['stats']['college'][0], "college_stats")
            
            norm_data[player['general']['name']] = {
                "general": player['general'],
                "physical": physical_stats,
                "combine": combine_stats,
                "college_stats": college_stats
            }
            
        return norm_data
    
class PlayerDataRefiner:
    def __init__(self):
        return
    
    def average(self, lst): 
        quant = len(lst)
        total = 0
        for elem in lst:
            if not elem:
                quant -= 1
                continue
            total += elem
        try:
            return total / quant
        except ZeroDivisionError:
            return None
    
    def refine_data(self, normalized_data):
        refined_data = {}
        for player, player_data in normalized_data.items():
            physical_data = player_data['physical']
            combine_data = player_data['combine']
            college_stats_data = player_data['college_stats']
            avg_physical = self.average(physical_data.values())
            avg_speed_accel = self.average([combine_data['40yd'], combine_data['10yd']])
            avg_explosive = self.average([
                combine_data['shuttle'],
                combine_data['vertical'],
                combine_data['broad'],
                combine_data['3cone']
            ])
            avg_catching = self.average([
                physical_data['hands'],
                physical_data['span'],
                college_stats_data['pff']['drop'],
                college_stats_data['ctc_pct'],
                college_stats_data['drop_pct']
            ])
            refined_data[player] = {
                'AVG Physical': avg_physical,
                "AVG Speed Acceleration": avg_speed_accel,
                "AVG Explosiveness": avg_explosive,
                "Norm RecV": college_stats_data['pff']['recv'],
                "AVG Catching": avg_catching,
                "NORM YAC": college_stats_data['yac_rec'],
                "NORM_YRR": college_stats_data['yds_rr'],
                "NORM SOS": college_stats_data['sos']
            }

        return refined_data

def process_and_sort_data(player_stats):
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(player_stats).T  # Transpose to get players as rows and stats as columns

    weights = [
        
    ]

    # Define a custom function to compute the new column based on existing stats
    def compute_new_metric(row):
        # Example computation: weighted sum of all metrics (customize as needed)
        return (row['AVG Catching'] + row['AVG Explosiveness'] + row['AVG Physical'] +
                row['AVG Speed Acceleration'] + row['NORM SOS'] + row['NORM YAC'] +
                row['NORM_YRR'] + row['Norm RecV']) / 8

    # Apply the function to each row to create the new column
    df['Computed Metric'] = df.apply(compute_new_metric, axis=1)

    # Sort the DataFrame by the new column in descending order
    df_sorted = df.sort_values('Computed Metric', ascending=False)

    # Print the sorted DataFrame
    print(df_sorted)

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

    # Refine player_data
    player_data_refiner = PlayerDataRefiner()
    refined_player_data = player_data_refiner.refine_data(normalized_players)
    pprint.pprint(refined_player_data)

    process_and_sort_data(refined_player_data)
import yaml
import pprint
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

class DataLoader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = self.load_data()

    def load_data(self):
        """Load data from a YAML file."""
        with open(self.file_name, 'r') as file:
            return yaml.safe_load(file)

class PlayerNormalizer:
    def __init__(self, norm_range_file):
        self.norm_ranges = DataLoader(norm_range_file).data['ranges']

    def normalize_value(self, outer_key, inner_key, value):
        """Normalize a value based on the normalization ranges."""
        if value is None:
            return None
        try:
            min_v, max_v, direction = self.norm_ranges[outer_key][inner_key]
            res = (value - min_v) / (max_v - min_v)
            if direction < 0:
                res = 1 - res
            return round(max(0, min(1, res)), 2)
        except KeyError:
            if isinstance(value, dict):
                return {
                    key: self.normalize_value(outer_key, inner_key + "_" + key, inner_value)
                    for key, inner_value in value.items()
                }
            #print(f"Normalization ranges for {outer_key} {inner_key} not found.")
            return value

    def normalize_stats(self, stats, category):
        """Normalize a dictionary of stats."""
        return {key: self.normalize_value(category, key, val) for key, val in stats.items()}

    def normalize_nfl_stats(self, stats, category):
        """Normalize NFL stats."""
        dict_to_return = {}
        for key, val in stats.items():
            if key == 'pff':
                dict_to_return['pff_recv'] = self.normalize_value(category, "pff_recv", val["recv"])
            elif key == 'ftn':
                dyar, dvoa = val.items()
                kiv_dyar, viv_dyar = dyar
                kiv_dvoa, viv_dvoa = dvoa
                dict_to_return[f'ftn_{kiv_dyar}'] = self.normalize_value(category, f'ftn_{kiv_dyar}', viv_dyar)
                dict_to_return[f'ftn_{kiv_dvoa}'] = self.normalize_value(category, f'ftn_{kiv_dvoa}', viv_dvoa)
            else:
                dict_to_return[key] = self.normalize_value(category, key, val)
        return dict_to_return

    def normalize_players(self, players_data):
        """Normalize player data."""
        norm_data = {}
        for player in players_data:
            if player['stats']['nfl'][0]:
                nfl_stats = self.normalize_nfl_stats(player['stats']['nfl'][0], "nfl_stats")
            else:
                nfl_stats = None
            physical_stats = self.normalize_stats(player['physical'], "physical")
            combine_stats = self.normalize_stats(player['combine'], "combine")
            college_stats = self.normalize_stats(player['stats']['college'][0], "college_stats")

            norm_data[player['general']['name']] = {
                "general": player['general'],
                "physical": physical_stats,
                "combine": combine_stats,
                "college_stats": college_stats,
                "nfl_stats": nfl_stats
            }
        return norm_data

class PlayerDataRefiner:
    @staticmethod
    def average(lst):
        """Calculate the average of a list, excluding None values."""
        valid_values = [elem for elem in lst if elem is not None]
        return round(sum(valid_values) / len(valid_values), 2) if valid_values else None

    @staticmethod
    def weighted_average(lst):
        """Calculate the weighted average of a list of tuples (weight, value), excluding None values."""
        total_weight = sum(weight for weight, elem in lst if elem is not None)
        total_value = sum(weight * elem for weight, elem in lst if elem is not None)
        return round(total_value / total_weight, 2) if total_weight > 0 else None

    def refine_data(self, normalized_data):
        """Refine the normalized player data."""
        refined_data = {}
        for player, player_data in normalized_data.items():
            physical_data = player_data['physical']
            combine_data = player_data['combine']
            college_stats_data = player_data['college_stats']
            nfl_data = player_data['nfl_stats']

            avg_physical = self.average(list(physical_data.values()))
            avg_speed_accel = self.average([combine_data['40yd'], combine_data['10yd']])
            
            if nfl_data:
                # nfl_avg = self.weighted_average([
                #     (2, nfl_data['yds_rr']),
                #     (1, nfl_data['yac_rec']),
                #     (4, nfl_data['yptoe']),
                #     (6, nfl_data['xfp_rr']),
                #     (8, nfl_data['pff_recv']),
                #     (5, nfl_data['ftn_dyar']),
                #     (3, nfl_data['ftn_dvoa']),
                # ])

                nfl_avg = nfl_data['pff_recv']
            else:
                nfl_avg = None

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
                'AVG Phys': avg_physical if avg_physical else 0.5,
                "AVG Spd Accl": avg_speed_accel if avg_speed_accel else 0.5,
                "AVG Explsv": avg_explosive if avg_explosive else 0.5,
                "Norm RecV": college_stats_data['pff']['recv'] if college_stats_data['pff']['recv'] else 0.5,
                "AVG Ctch": avg_catching if avg_catching else 0.5,
                "NORM YAC": college_stats_data['yac_rec'] if college_stats_data['yac_rec'] else 0.5,
                "NORM_YRR": college_stats_data['yds_rr'] if college_stats_data['yds_rr'] else 0.5,
                "NORM SOS": college_stats_data['sos'] if college_stats_data['sos'] else 0.5,
            }

            if nfl_data: 
                refined_data[player].update({
                    "NFL YPRR": nfl_data['yds_rr'],
                    "NFL YAC": nfl_data['yac_rec'],
                    "NFL_YPTOE": nfl_data['yptoe'],
                    "NFL_XFPRR": nfl_data['xfp_rr'],
                    "NFL_PFF": nfl_data['pff_recv'],
                    "NFL_DYAR": nfl_data['ftn_dyar'],
                    "NFL_DVOA": nfl_data['ftn_dvoa'],
                    "NFL RR": nfl_data['rr']['total'],
                    "NFL": nfl_avg
                })
            # else:
            #     refined_data[player].update({
            #         "NFL YPRR": None,
            #         "NFL YAC": None,
            #         "NFL_YPTOE": None,
            #         "NFL_XFPRR": None,
            #         "NFL_PFF": None,
            #         "NFL_DYAR": None,
            #         "NFL_DVOA": None,
            #         "NFL RR": None
            #     })

        return refined_data
    

def separate_players(refined_player_data, min_routes_run=0):
    """Separate players into two groups based on the availability of NFL stats."""
    players_with_nfl_stats = {}
    players_without_nfl_stats = {}

    for player, player_data in refined_player_data.items():
        pprint.pprint(player_data)
        if 'NFL' in player_data:
            if player_data['NFL RR'] >= min_routes_run:
                players_with_nfl_stats[player] = player_data
        else:
            players_without_nfl_stats[player] = player_data

    print(len(players_with_nfl_stats))
    return players_with_nfl_stats, players_without_nfl_stats

def create_train_test_data(players_with_nfl_stats, random_state, degree=2):
    """Create training and testing data for the regression model."""
    df = pd.DataFrame(players_with_nfl_stats).T

    X = df[['AVG Phys', 'AVG Spd Accl', 'AVG Explsv', 'Norm RecV', 'AVG Ctch', 'NORM YAC', 'NORM_YRR', 'NORM SOS']]
    y = df['NFL']

    # Create polynomial features
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_poly, y, test_size=0.2, random_state=random_state)

    return X_train, X_test, y_train, y_test

def train_regression_model(X_train, y_train):
    """Train the regression model."""
    model = LinearRegression(
        positive=True,
        fit_intercept=False
    )
    model.fit(X_train, y_train)
    return model

def predict_nfl_stats(model, players_without_nfl_stats, poly):
    """Predict NFL stats for players without NFL stats using the regression model."""
    df = pd.DataFrame(players_without_nfl_stats).T
    X = df[['AVG Phys', 'AVG Spd Accl', 'AVG Explsv', 'Norm RecV', 'AVG Ctch', 'NORM YAC', 'NORM_YRR', 'NORM SOS']]

    # Apply the same polynomial transformation
    X_poly = poly.transform(X)

    predicted_nfl_stats = model.predict(X_poly)
    df['Predicted NFL'] = predicted_nfl_stats

    # Sort the DataFrame by the predicted NFL score in descending order
    df = df.sort_values('Predicted NFL', ascending=False)

    return df

def evaluate_model(model, X_test, y_test):
    """Evaluate the model's performance on the test data."""
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"R-squared (R2) Score: {r2:.4f}")
    residuals = y_test - y_pred

    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals)
    plt.title('Residual Plot')
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.axhline(y=0, color='r', linestyle='--')
    plt.show()



if __name__ == '__main__':
    norm_range_set = 'norm_ranges.yaml'
    players_data_set = 'cfb.yaml'

    player_data_loader = DataLoader(players_data_set)
    players_data = player_data_loader.data['players']

    player_normalizer = PlayerNormalizer(norm_range_set)
    normalized_players = player_normalizer.normalize_players(players_data)

    player_data_refiner = PlayerDataRefiner()
    refined_player_data = player_data_refiner.refine_data(normalized_players)

    players_with_nfl_stats, players_without_nfl_stats = separate_players(refined_player_data)

    # # Print players with NFL stats
    # print("Players with NFL Stats:")
    # pprint.pprint(players_with_nfl_stats)
    # players_with_nfl_stats_df = pd.DataFrame(players_with_nfl_stats).T
    # players_with_nfl_stats_df = players_with_nfl_stats_df[['AVG Phys', 'AVG Spd Accl', 'AVG Explsv', 'Norm RecV', 'AVG Ctch', 'NORM YAC', 'NORM_YRR', 'NORM SOS', 'NFL']]
    # print(players_with_nfl_stats_df)
    # print()

    # for num in range(100):
    #     print(f"Using random_state: {num}")
    #     # Create training and testing data
    #     X_train, X_test, y_train, y_test = create_train_test_data(players_with_nfl_stats, num)

    #     # Train the regression model
    #     model = train_regression_model(X_train, y_train)

    #     # Evaluate the model on the test data
    #     evaluate_model(model, X_test, y_test)
    #     print()

    # # # Predict NFL stats for players without NFL stats
    # predicted_nfl_stats = predict_nfl_stats(model, players_without_nfl_stats)
    # # print("Predicted NFL Stats:")
    # # print(predicted_nfl_stats)

    poly = PolynomialFeatures(degree=2, include_bias=False)

    # Create training and testing data
    X_train, X_test, y_train, y_test = create_train_test_data(players_with_nfl_stats, random_state=42, degree=2)

    # Train the regression model
    model = train_regression_model(X_train, y_train)

    # Evaluate the model
    evaluate_model(model, X_test, y_test)

    # Predict NFL stats for players without NFL stats
    predicted_nfl_stats = predict_nfl_stats(model, players_without_nfl_stats, poly)

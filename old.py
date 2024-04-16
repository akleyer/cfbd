from __future__ import print_function
import time
import cfbd
from cfbd.rest import ApiException
from pprint import pprint

# Configure API key authorization: ApiKeyAuth
configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = 'qoZ1oUxGmh3tPDnZLRdRemn/4ctKiS65P2SHSN4fh/yhINUH5rDWjyf7edI96kq+'
configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = cfbd.PlayersApi(cfbd.ApiClient(configuration))
year = 2022 # int | Year filter
#team = 'team_example' # str | Team filter (optional)
#conference = 'conference_example' # str | Conference abbreviation filter (optional)
#start_week = 56 # int | Start week filter (optional)
#end_week = 56 # int | Start week filter (optional)
season_type = 'both' # str | Season type filter (regular, postseason, or both) (optional)
category = 'receiving' # str | Stat category filter (e.g. passing) (optional)

try:
    # Player stats by season
    api_response = api_instance.get_player_season_stats(
        year,
        #team=team,
        #conference=conference,
        #start_week=start_week,
        #end_week=end_week,
        season_type=season_type,
        category=category
    )

    organize_players = {}
    for elem in api_response:
        dict_elem = elem.to_dict()
        if dict_elem['player'] not in organize_players:
            organize_players[dict_elem['player']] = {
                "Conference" : dict_elem['conference'],
                "Player_ID" : dict_elem['player_id'],
                "Team" : dict_elem['team']
            }
        organize_players[dict_elem['player']][dict_elem['stat_type']] = dict_elem['stat']

        search_term = dict_elem['player']
        player_search_api_response = api_instance.player_search(
            search_term,
            # position=position,
            team=dict_elem['team'],
            # year=year
        )

        try:
            player_elem = player_search_api_response[0].to_dict()
        except IndexError:
            print(dict_elem['player'])
            continue

        organize_players[dict_elem['player']]['Height'] = player_elem['height']
        organize_players[dict_elem['player']]['Position'] = player_elem['position']
        organize_players[dict_elem['player']]['Weight'] = player_elem['weight']


    pprint(organize_players)

except ApiException as e:
    print("Exception when calling PlayersApi->get_player_season_stats: %s\n" % e)

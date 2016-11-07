import ujson as json
import numpy
import cPickle as pickle


most_recent_2016_week = 8
ranker_ids = ['113', '120', '125', '127', '317', '387', '406', '43', '475', '64']


def get_raw_data():
    with open('raw_rankings_and_stats.json', 'rb') as raw_file:
        raw_data = json.load(raw_file)
    return raw_data


class Week:
    def __init__(self, year, week, raw_data=get_raw_data()):
        self.year = year
        self.week = week
        self.qbs = get_players(self.year, self.week, 'QB', raw_data)
        self.rbs = get_players(self.year, self.week, 'RB', raw_data)
        self.wrs = get_players(self.year, self.week, 'WR', raw_data)
        self.tes = get_players(self.year, self.week, 'TE', raw_data)
        self.flexes = get_players(self.year, self.week, 'FLX', raw_data)
        self.dsts = get_players(self.year, self.week, 'DST', raw_data)


class PlayerWeek:
    def __init__(self, name, p_dict, position):
        self.name = name
        self.actual_rank = p_dict['actual_rank']
        self.rankings = p_dict['rankings']
        self.actual_points = p_dict['actual_points']
        self.team = p_dict['team']
        self.position = position

    def __str__(self):
        output = '====\n' + self.name
        output += '\nPoints scored: ' + str(self.actual_points)
        output += '\nActual rank: ' + str(self.actual_rank)
        output += '\nMedian pred: ' + str(numpy.nanmedian(self.rankings.values()))
        output += '\nPredicted: ' + str(self.rankings.values())
        return output


def print_week(player_dictionary):
    for player, stats in player_dictionary.iteritems():
        print('====\n' + player)
        print('Actual rank: ' + str(stats['actual_rank']))
        print('Predicted: ' + str(stats['rankings'].values()))


def get_players(year, week, position, raw_data):
    """
    Takes as inputs the year, week, and positions needed
    Parses through the raw json and
    Returns a list of player objects for that week's position
    The list is sorted by points scored
    """

    actual_stats = get_actuals(year, week, position, raw_data)
    predictions = get_predictions(year, week, position, raw_data)

    player_list = []

    for player_name in actual_stats.keys():
        # If the player doesn't apper in any expert's rankings, add them
        # with no rankings
        if player_name not in predictions.keys():
            predictions[player_name] = {'rankings': {}}
        player_predictions = predictions[player_name]['rankings']

        for ranker_id in ranker_ids:
            # The machine learning input needs missing info to be NaN
            # So if experts haven't ranked a player that value is NaN
            if ranker_id not in player_predictions.keys():
                player_predictions[ranker_id] = float('nan')
        for k, v in predictions[player_name].iteritems():
            actual_stats[player_name][k] = v

        current_player = PlayerWeek(player_name, actual_stats[player_name], position)
        player_list.append(current_player)

    player_list = sorted(player_list, key= lambda p: p.actual_points, reverse=True)

    return player_list


def get_predictions(year, week, position, raw_data):
    """
    Does some initial parsing of the raw data to create a name:rankings dictionary
    For each player that received rankings in that position in that week
    """

    response_object = raw_data[year][week][position]['predictions']

    players = {}

    for player in response_object['players']:
        name = player['player_name']
        rankings = {}
        for k, v in player['experts'].iteritems():
            rankings[k] = int(v)
        team = player['player_team_id']
        players[name] = {'rankings': rankings, 'team': team}

    return players


def get_actuals(year, week, position, raw_data):
    if position != 'FLX':
        return raw_data[year][week][position]['actuals']
    flex_dict = {}
    all_points = []
    for k, v in raw_data[year][week]['RB']['actuals'].iteritems():
        flex_dict[k] = v
        all_points.append(v['actual_points'])
    for k, v in raw_data[year][week]['WR']['actuals'].iteritems():
        flex_dict[k] = v
        all_points.append(v['actual_points'])
    for k, v in raw_data[year][week]['TE']['actuals'].iteritems():
        flex_dict[k] = v
        all_points.append(v['actual_points'])

    all_points.sort(reverse=True)
    for k, v in flex_dict.iteritems():
        v['actual_rank'] = all_points.index(v['actual_points']) + 1

    return flex_dict


def get_all_weeks(serialize=False):
    all_weeks = []
    raw_data = get_raw_data()

    year = 2015
    for week in [str(i) for i in range(1, 17)]:
        all_weeks.append(Week(year, week, raw_data))

    year = 2016
    for week in [str(i) for i in range(1, most_recent_2016_week)]:
        all_weeks.append(Week(year, week, raw_data))

    if serialize:
        with open('fantasy-stats-2015-2016-wk8.pickle') as outfile:
            pickle.dump(all_weeks, outfile, pickle.HIGHEST_PROTOCOL)
    return all_weeks

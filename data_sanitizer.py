import ujson as json
import numpy
import cPickle as pickle


most_recent_2016_week = 8
ranker_ids = ['113', '120', '125', '127', '317', '387', '406', '43', '475', '64']


def get_raw_data():
    with open('raw_rankings_and_stats.json', 'rb') as raw_file:
        raw_data = json.load(raw_file)
    return raw_data

class AllWeeks:
    def __init__(self):
        self.weeks = get_all_stats_dict()

    def get_week(self, year, week):
        return self.weeks[year][week]

    def all_data_lists(self):
        output = []
        for week in self.get_all_weeks():
            output += week.data_lists()
        return output

    def all_swapped_data_lists(self):
        data_lists = []
        for week in self.get_all_weeks():
            data_lists += week.swapped_data_lists()
        return data_lists

    def get_all_weeks(self):
        all_weeks = []
        for year, weeks in self.weeks.iteritems():
            for week_number, week in weeks.iteritems():
                all_weeks.append(week)
        return all_weeks


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
        self.position_dict = {'QB': self.qbs, 'RB': self.rbs, 'WR': self.wrs,
                              'TE': self.tes, 'FLX': self.flexes, 'DST': self.dsts}

        self.add_swapped_data_to_players()


    def add_swapped_data_to_players(self):
        for player in self.all_players():
            player_data = player.data_list()
            swapped_data = []
            # Skipping the last item in player data b/c that one has the player's points
            for index, predicted_rank in enumerate(player_data[:-1]):
                swapped_data.append(self.get_rank_actual_points(
                    player.position, predicted_rank))
            player.swapped_predictions = swapped_data



    def data_lists(self):
        # Returns a list of rankings ending in the value of the actual score or
        # the actual rank
        # This method exists to clean up the data for fitting prediction models
        return [player.data_list() for player in self.all_players()]


    def swapped_data_lists(self):
        # This method returns a list of values that replaces each ranker's rank
        # with the actual score that the player at that position in that rank scored
        data_lists = []
        for player in self.all_players():
            player_data = player.data_list()
            # Skipping the last item in player data b/c that one has the player's points
            for index, predicted_rank in enumerate(player_data[:-1]):
                player_data[index] = self.get_rank_actual_points(
                    player.position, predicted_rank)
            data_lists.append(player_data)
        return data_lists

    def all_players(self):
        return self.qbs + self.rbs + self.wrs + self.tes + self.flexes + self.dsts

    def get_rank_actual_points(self, position, rank):
        for player in self.position_dict[position]:
            if player.actual_rank == rank:
                return player.actual_points
        # print(position, rank)
        return 0

class PlayerWeek:
    def __init__(self, name, p_dict, position):
        self.name = name
        self.actual_rank = p_dict['actual_rank']
        self.rankings = p_dict['rankings']
        self.actual_points = p_dict['actual_points']
        self.team = p_dict['team']
        self.position = position
        # Swapped predictions means that the expert's ranking is swapped with the
        # actual points of the player at that position and that rank for the week
        # This remains an empty list until the add_swapped_data_to_players() function
        # of Week is called
        self.swapped_predictions = []

    def __str__(self):
        output = '====\n' + self.name
        output += '\nPoints scored: ' + str(self.actual_points)
        output += '\nActual rank: ' + str(self.actual_rank)
        output += '\nMedian pred: ' + str(numpy.nanmedian(self.rankings.values()))
        output += '\nPredicted: ' + str(self.rankings.values())
        return output

    def data_list(self, rank=False):
        # If rank is false, add the actual points to this data list in the last slot
        # If it's true, we add the rank here in the last slot
        data = []
        # Sorting the keys here so that each ranker always has the same list index
        for ranker_key in sorted(self.rankings.keys()):
            data.append(self.rankings[ranker_key])
        if rank:
            data.append(self.actual_rank)
        else:
            data.append(self.actual_points)
        return data


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
    # TODO: This assigns the rank to the place in all_points where that number of points
    # appears first, so it assigns the same rank to multiple players
    # and some ranks have no players
    already_given_ranks = set()
    for k, v in flex_dict.iteritems():

        found_rank = all_points.index(v['actual_points']) + 1
        while True:
            if found_rank not in already_given_ranks:
                v['actual_rank'] = found_rank
                already_given_ranks.add(found_rank)
                break
            else:
                found_rank += 1

    return flex_dict


def get_all_weeks(serialize=False):
    all_weeks = []
    raw_data = get_raw_data()

    year = '2015'
    # TODO: The scraper had a bug where it didn't get week 17, re-run scraper
    # and change the 17 below to 18
    for week in [str(i) for i in range(1, 17)]:
        all_weeks.append(Week(year, week, raw_data))

    year = '2016'
    # TODO: Same thing as above here
    for week in [str(i) for i in range(1, most_recent_2016_week)]:
        all_weeks.append(Week(year, week, raw_data))

    if serialize:
        with open('fantasy-stats-2015-2016-wk8.pickle') as outfile:
            pickle.dump(all_weeks, outfile, pickle.HIGHEST_PROTOCOL)
    return all_weeks

def get_all_stats_dict():
    all_weeks = {}
    raw_data = get_raw_data()

    year = '2015'
    all_weeks['2015'] = {}
    # TODO: The scraper had a bug where it didn't get week 17, re-run scraper
    # and change the 17 below to 18
    for week in [str(i) for i in range(1, 17)]:
        all_weeks[year][week] = Week(year, week, raw_data)

    year = '2016'
    all_weeks['2016'] = {}
    # TODO: Same thing as above here
    for week in [str(i) for i in range(1, most_recent_2016_week)]:
        all_weeks[year][week] = Week(year, week, raw_data)

    return all_weeks

from bs4 import BeautifulSoup
import requests
import ujson as json
import time
import random


ranker_ids = ['113', '120', '125', '127', '317', '387', '406', '43', '475', '64']

def get_predictions(year, week, position):
    """
    Generates and executes the request to the fantasypros api for the rankings of
    players of a certain position in a year and week
    Returns the 'players' object from the response, which is a list of player
    dictionaries with information about each player and the five experts' rankings
    of them
    """

    # These are the most accurate rankers from the last three years from Fantasy Pros
    expert_ids = ''
    for expert_id in ranker_ids:
        expert_ids += expert_id + ':'
    expert_ids = expert_ids[:-1]

    req_params = {
        'experts': 'show',
        'sport': 'NFL',
        'year': year,
        'week': week,
        'id': '146',
        'position': position,
        'type': 'ST',
        'scoring': '',
        'filters': expert_ids,
        'callback': 'FPW.rankingsCB'
    }

    request_url = 'http://partners.fantasypros.com/api/v1/consensus-rankings.php'

    response = requests.get(request_url, params=req_params)

    # Cropping the response text to get to the json
    raw_json_response = response.text[response.text.find('{') : -2]

    response_object = json.loads(raw_json_response)

    return response_object

def get_actual_stats(year, week, position):
    """
    Goes to the fftoday.com site and scrapes actual points and rankings for each player
    :param year: season year as a string
    :param week: season week as a string
    :param position: 'QB', 'RB', etc.
    :return: dictionary of player's name to their points and ranking for the week
    """
    pos_dict = {
        'QB': 10,
        'RB': 20,
        'WR': 30,
        'TE': 40,
        'DST': 99
    }

    fftoday_url = 'http://www.fftoday.com/stats/playerstats.php?'
    ff_params = {
        'Season': year,
        'GameWeek': week,
        'PosID': pos_dict[position],
        'LeagueID': '1'
    }

    response = requests.get(fftoday_url, params=ff_params)
    ff_soup = BeautifulSoup(response.text, 'html.parser')
    tables = ff_soup.find_all('table')
    stats_table = tables[9]
    player_rows = stats_table.find_all('tr')[3:]

    # Key is player's full name, value is a list containing the rank and the points
    actual_scores = {}


    for i in range(len(player_rows)):
        row = player_rows[i]
        week_rank = i + 1
        name = row.find('a').text
        team = row.find_all('td')[1].text
        points = float(row.find_all('td')[-1].text)
        actual_scores[name] = {'actual_points': points,
                               'actual_rank': i + 1,
                               'team': team}

    return actual_scores


def scrape_all():

    raw_data = {}

    for year in ['2015', '2016']:
        raw_data[year] = {}
        max_week = {'2015': 17, '2016': 8}
        for week in [str(i) for i in range(1, max_week[year])]:
            raw_data[year][week] = {}
            for position in ['QB', 'RB', 'WR', 'FLX', 'TE', 'DST']:
                print('#######################\n' + year + ' ' + week + ' ' + position)
                position_week = {}
                position_week['predictions'] = get_predictions(year, week, position)
                # There's no web page to scrape for flex players, will need to combine
                # the actual stats for WR, RB, and TE to make this one
                if position != 'FLX':
                    position_week['actuals'] = get_actual_stats(year, week, position)
                else:
                    position_week['actuals'] = {}
                raw_data[year][week][position] = position_week
                # pprint(raw_data)
                # Stop execution for a while in order to be polite to the servers
                time.sleep(random.randint(20, 100) + random.random())

    with open('raw_rankings_and_stats.json', 'wb') as outfile:
        json.dump(raw_data, outfile)


if __name__ == '__main__':
    scrape_all()
"""
In this file we'll create the machine learning model that takes
predictions as inputs and rnakings as outputs
"""

import data_sanitizer
import numpy
import pandas
from keras.models import Sequential
from keras.layers import Dense

from sklearn import linear_model
from sklearn import svm
from sklearn import neural_network


# data = [numpy.array(item) for item in data if numpy.count_nonzero(item) > 5]
# define base model
def print_model(model, week):
    players = week.flexes
    predictions = model.predict([player.swapped_predictions for player in players])
    # Associating each player with their prediction so we can rank the predictions
    player_prediction_tuples = []
    for index, player in enumerate(players):
        player_prediction_tuples.append((player, predictions[index]))

    ranked_prediction_tuples = sorted(player_prediction_tuples, key=lambda k: k[1], reverse=True)
    # So I'm getting the rank of each player based on the regression's predicted score
    # for that player
    # Then I'm saying that the regression's prediction for that player is the value of the
    # actual points scored by the player at that position in that rank for that week
    for index, tup in enumerate(ranked_prediction_tuples):
        player = tup[0]
        print('=' + str(index + 1) + '==========================================')
        print(player.name)
        print('Experts: ' + str(player.swapped_predictions))
        # Index + 1 is the rank of the player, since we sorted by regression prediction
        print('Prediction: ' + str(week.get_rank_actual_points(player.position, index + 1)))
        print('Actual points: ' + str(player.actual_points))



def make_models():

    all_weeks = data_sanitizer.AllWeeks()
    # load dataset
    dataset = numpy.array(all_weeks.all_swapped_data_lists())

    # These are all the players with rankings from every expert
    dataset = [numpy.array(item) for item in dataset
               if numpy.count_nonzero(item) == 11
               and not numpy.isnan(item.sum())]
    dataset = numpy.array(dataset)
    # Our inputs here are the expert rankings of each player
    input_vars = dataset[:, 0:-1]
    # The output values are the actual rankings of each player
    output_var = dataset[:, -1]

    test_week = all_weeks.get_week('2016', '7')

    print('\n=====================')
    print('============Ordinary Least Squares=============')
    ols = linear_model.LinearRegression()
    ols.fit(input_vars, output_var)
    print_model(ols, test_week)

    print('\n=====================')
    print('============Ridge Regression=============')
    ridge = linear_model.Ridge()
    ridge.fit(input_vars, output_var)
    print_model(ridge, test_week)

    print('\n=====================')
    print('============Passive Aggressive Regression=============')
    par = linear_model.PassiveAggressiveRegressor()
    par.fit(input_vars, output_var)
    print_model(par, test_week)

    print('\n=====================')
    print('============Multi-Layer Perceptron=============')
    mlp = neural_network.MLPRegressor()
    mlp.fit(input_vars, output_var)
    print_model(mlp, test_week)

if __name__ == '__main__':
    make_models()
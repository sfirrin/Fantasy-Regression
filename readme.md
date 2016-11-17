# Fantasy Regression

Can we use the predictions of the most accurate fantasy football experts to generate a model that can more accurately predict the fantasy points scored by players? If so, which regression model is best?

Fantasy Regression does the following:

1. Scrapes together the predictions of the top 10 most accurate fantasy football experts according to their ranking accuracy as determined by fantasypros.com 
  * Unfortunately, it would be too time consuming to go back farther than the 2015 season - I'd like to do this in the future to see if it improves the models)

2. Scrapes the actual fantasy points scored by players

3. Uses the expert ranking predictions for weeks in the 2015 season as inputs and the actual points as outputs to generate several regression models included in the scikit-learn Python library

4. Uses the experts' ranking predictions for weeks in the 2016 season as inputs to generate predictions from the models

5. Evaluates the models' predictions and compare them to one another as well as the experts' individual predictions

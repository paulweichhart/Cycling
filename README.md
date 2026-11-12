# MLZoomcamp Midterm Project Cycling

This repository is the home of the MLZoomcamp Midterm Project for Machine Learning. In general, this project uses linear regression to predict the VO2max value for cycling activity.

## Problem
If you are obsessed with your VO2max value & trained all year on your bike with your Apple Watch, you ended up with no value at all. Apple mentions in the documentation that the prediction is too weak while cycling in order to calculate it. This is the foundation for this project.

## Approach
After some evaluation, I found a promising dataset available at https://zenodo.org/records/10841412 with data on running, rowing, kayaking & cycling. The data itself can be found under data/xlsx. For evaluation, plotting & feature extraction, data/utils/build_cycling_csv.py & data/utils/exploratory_data_analysis.py were used. The final .csv containing the data can be found at data/cycling_tests.csv, which was used for training the model.

As the target value is numeric, linear regression is the right tool at hand. For the distribution of the data please see data/utils/plot.png.

While the course expects a service to return the value, this project also contains a web form for a better experience.

## Training
While quite a few features were extracted from the dataset, only "gender", "age", "weight", "mean_hr", "mean_power_per_kg" were used for training the model. In general, Scikit-Learn was used for applying linear regression with the following configuration:
* one-hot encoding for gender (DictVectorizer(sparse=False))
* 60/20/20 train, validation & test split (train_test_split)
* Joblib for storing the model
* coef, mse, r2 for evaluating and fine-tuning the model
* StandardScaler was used for better feature scaling of the model

The training is located at src/utils/train_model.py & the model can be trained by calling `cd src && ../.venv/bin/python -m utils.train_model`

After running multiple cross-validations, the mean squared error using Linear Regression is `4.5399` & r2 is `0.705`. Check Hyperparameter Tuning for more details on the best model.

The web service can be found in src/service & is available at cyclingapi.paulweichhart.com, hosted on Vercel.

## Hyperparameter Tuning

Model                                      | Result
-------------------------------------------|---------------------
Linear Regression 60/20/20                 | MSE 4.540, R2 0.705
GradientBoostingRegressor cross-validation | MSE 4.789, R2 0.666
Linear Regression KFold                    | MSE 4.793, R2 0.669
RandomForestRegressor cross-validation     | MSE 4.809, R2 0.664
DecisionTreeRegressor cross-validation     | MSE 5.205, R2 0.606

For GradientBoostingRegressor, RandomForestRegressor & DecisionTreeRegressor, different leaves, depths, learning rates & estimators were chosen to find the best model.

## Experience
Since `POST` onto a web service isn't fun or a great experience, Claude supported me in providing a web form using Python Django. The form is hosted on Vercel and available at: http://cycling.paulweichhart.com


## Docker

Docker File & ignore have been added — use the following commands for building & running:
`docker build -t cyclingapi`
`docker run --rm -p 8080:8080 cyclingapi`
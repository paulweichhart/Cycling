# MLZoomcamp Midterm Project Cycling

This Repository is the home of the MLZoomCamp Midterm Project for Machine Learning. In general, this project uses linear regression to predict the VO2max value for cycling activity.

## Problem
If you are obsessed with your VO2max value & trained all year on your bike with your Apple Watch, you ended up with no value at all. Apple mentions in the Documentation that the prediction is too weak in order to calculate it. This is the foundation for this project.

## Approach
After some evaluation, I found a promising Data Set available at https://zenodo.org/records/10841412 with data on running, rowing, kayaking & cycling. The Data itself can be found under data/xlsx. For evaluation, plotting & feature extraction, data/utils/build_cycling_csv.py & data/utils/exploratory_data_analysis.py was used. The final .csv containing the data can be found at data/cycling_tests.csv which was used for training the model.

As the target value is numeric, linear regression is the right tool at hand. For distribution of the data please see data/utils/plot.png.

While the course expects a service to return the value, this project also contains a webform for better experience.

## Training
While quite a few features were extracted from the dataset, only "gender", "age", "weight", "mean_hr", "mean_power_per_kg" were used for training the model. In general, Scikit-Learn was used for applying linear regression with the following configuration:
* one-hot-encoding for Gender (DictVectorizer(sparse=False))
* KFold with 5 splits and shuffle
* Joblib for storing the model
* coef, mse, r2 for evaluating and fine tuning the model
* StandardScaler was used for better feature tuning of the model 

The training is located at src/utils/train_model.py & the model can be trained by calling `cd src && ../.venv/bin/python -m utils.train_model`

Currently the mean squared error is `4,79` & r2 is `0.699`. While the values were better with a classic 80/20 training & validation split, using KFold felt like the right approach for splitting the data.

The webservice can be found in src/service & is available at cyclingapi.paulweichhart.com hosted on Vercel.

## Experience
Since `post` onto a webservice isn't fun or a great experience, claude supported me in providing a webform using python django. The form is hosted on Vercel and available at: http://cycling.paulweichhart.com








 


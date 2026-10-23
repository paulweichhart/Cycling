import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression

class MachineLearning:
	
	@staticmethod
	def explore_data(data, column):
		print(len(data))
		print(data.head())
		
		# plt.figure(figsize=(6, 4))
		
		# sns.histplot(data[column], bins=40, color='black', alpha=1)
		# plt.xlabel(column)
		# plt.title(column)
		
		# plt.show()
		
		print(f"min: {data[column].min()} max: {data[column].max()}")
	
	@staticmethod
	def split_data(df_data, seed=42):        
		n = len(df_data)
		n_val = int(n * 0.2)
		n_test = int(n * 0.2)
		n_train = n - n_val - n_test
		
		np.random.seed(seed)
		idx = np.arange(n)
		np.random.shuffle(idx)
		
		df_train = df_data.iloc[idx[:n_train]].reset_index(drop=True)
		df_val = df_data.iloc[idx[n_train:n_train + n_val]].reset_index(drop=True)
		df_test = df_data.iloc[idx[n_train + n_val:]].reset_index(drop=True)
		
		return df_train, df_val, df_test
	
	@staticmethod
	def prepare_target(df_train, df_val, df_test, column):
		y_train = df_train[column].values
		y_val = df_val[column].values
		y_test = df_test[column].values
		return y_train, y_val, y_test 
		
	@staticmethod
	def prepare_data(df_train, df_val, df_test, column, fillna=0):
		del df_train[column]
		del df_val[column]
		del df_test[column]
		
		return df_train.fillna(fillna).values, df_val.fillna(fillna).values, df_test.fillna(fillna).values
		
	@staticmethod
	def train_model(X, y)
	
	@staticmethod
	def predict(X, y)
	
	@staticmethod
	def rmse(y, y_pred)
		error = y_pred - y
		mse = (error ** 2).mean()
		return np.sqrt(mse)
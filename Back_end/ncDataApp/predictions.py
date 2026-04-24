from django.db import models
import json
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import xarray as xr
import pandas as pd
import numpy as np
from dateutil import rrule
from datetime import datetime, timedelta
#import the necessary libraries and modules for prediction
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

class PredictionModel():
    def nc_prediction(self,request, ERA5_df, H2OSOI_df, input_date,nearest_index):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        lat = round(float(np.array(body['lat'])))
        lon = round(float(np.array(body['lon'])))
        Latitude = lat
        Longitude = lon+360
        Lead_Val = str(np.array(body['soilLevel']))
        if(Lead_Val == ''):
            Lead_Val = 7
        else:
            Lead_Val = int(Lead_Val)
        
        def gen_data(X, y, num_steps=1): # def gen_data(1200, 1200, 7):
            Xs, ys = [], [] # two empty lists
            for i in range(len(X) - num_steps): # for i in range(1200 - 7):
                stacked_data = X.iloc[i:num_steps+i-1, :num_steps].stack() # stacked_data = X.iloc[0:7+0-1, :7].stack()
                Merged_data = stacked_data.reset_index(drop=True) # reset index values
                Xs.append(Merged_data) # Append data to Xs
                ys.append(y.iloc[num_steps+i-1, :]) # ys.append(np.array(y.iloc[7+0-1, :]))
            return Xs, ys # return Xs and ys to dataX and dataY

        # Num of row steps
        num_steps = int(Lead_Val) # because we took only first 7 columns (7 days)
        dataX, dataY = gen_data(ERA5_df, ERA5_df, num_steps) # dataX, dataY = gen_data(1200, 1200, 7)
        dataX = pd.DataFrame(dataX)
        dataY = np.array(dataY, dtype=np.float32)
        # if(Lead_Val == 7):
        #     model = tf.keras.models.load_model("Best_Model/Lead_7/model__saved_for_1200_rows_Prediction_Lead_"+str(Lead_Val)+".h5")
        #     # model = tf.keras.models.load_model("Best_Model/model__saved_for_1200_rows_Prediction.h5")
        # elif(Lead_Val == 21):
        #     model = tf.keras.models.load_model("Best_Model/Lead_21/model__saved_for_1200_rows_Prediction_Lead_"+str(Lead_Val)+".h5")

        model = tf.keras.models.load_model("Best_Model/Whole_US/Best_Model_"+str(nearest_index)+".h5")
        predicted_data = model.predict(dataX)
        pred = pd.DataFrame(predicted_data)
        dataY_1 = pd.DataFrame(dataY)
        
        def get_monday_date(df, input_date):
            # Parse the input date
            # input_date = datetime.strptime(str(input_date), "%Y-%m-%d")

            # Get the start date of the DataFrame
            start_date = datetime(1999, 1, 4)  # Assuming the 0th row starts on 4/1/1999

            # Calculate the number of days between the input date and the start date
            days_difference = (input_date - start_date).days

            # Calculate the number of weeks
            week_number = days_difference // 7

            # Calculate the Monday date for the given week
            monday_date = start_date + timedelta(days=week_number * 7)

            return monday_date.strftime("%Y-%m-%d"),week_number
        monday_date,week_number = get_monday_date(H2OSOI_df, input_date)
        
        # Date Formation
        end_46th_date = str(pd.to_datetime(monday_date)+ timedelta(days=45))
        monday_date = str(monday_date)
        print("-----------------------------------")
        print("Monday date",monday_date)
        print("-----------------------------------")
        Date = pd.date_range(start= monday_date,end= end_46th_date)
        print("end date",end_46th_date)
        Date_df = pd.DataFrame(Date)
        pred = pred.iloc[week_number]    
        ERA5_df = ERA5_df.iloc[week_number]
        H2OSOI_df = H2OSOI_df.iloc[week_number]

        Combined_df = pd.concat([Date_df,ERA5_df,H2OSOI_df,pred],axis=1)
        Combined_df.columns = ['Date','ERA5','H2OSOI','predictions']

        def anomaly_correlation_coefficient(model_data, observed_data):
            # Calculate the mean along the time axis
            model_mean = np.mean(model_data, axis=0)
            observed_mean = np.mean(observed_data, axis=0)

            # Calculate the anomalies by subtracting the mean
            model_anomalies = model_data - model_mean
            observed_anomalies = observed_data - observed_mean

            # Calculate the ACC
            numerator = np.sum(model_anomalies * observed_anomalies)
            denominator = np.sqrt(np.sum(model_anomalies**2) * np.sum(observed_anomalies**2))
            acc = numerator / denominator

            return acc
        # Calculate Mean Absolute Error (MAE)
        mae = round(mean_absolute_error(Combined_df['ERA5'], Combined_df['predictions']),2)

        # Calculate Root Mean Squared Error (RMSE)
        rmse = round(np.sqrt(mean_squared_error(Combined_df['ERA5'], Combined_df['predictions'])),2)

        acc = round(anomaly_correlation_coefficient(Combined_df['ERA5'], Combined_df['predictions']),2)
        Evaluation_metrics = {
            'MAE': mae,
            'RMSE': rmse,
            'ACC': acc
        }
        evaluation_metrics_df = pd.DataFrame([Evaluation_metrics])
        return Combined_df,evaluation_metrics_df
    
    def nc_prediction_model_2(self,request, ERA5_df, H2OSOI_df, input_date,nearest_index):
        def gen_data(X, y, num_steps=1): # def gen_data(1200, 1200, 7):
            Xs, ys = [], [] # two empty lists
            for i in range(len(X) - num_steps): # for i in range(1200 - 7):
                stacked_data = X.iloc[i:num_steps+i-1, :num_steps].stack() # stacked_data = X.iloc[0:7+0-1, :7].stack()
                Merged_data = stacked_data.reset_index(drop=True) # reset index values
                Xs.append(np.array(Merged_data, dtype=object)) # Append data to Xs
                ys.append(np.array(y.iloc[num_steps+i-1, :])) # ys.append(np.array(y.iloc[7+0-1, :]))
            return np.array(Xs, dtype=object), np.array(ys, dtype=object) # return Xs and ys to dataX and dataY

        # Num of row steps
        num_steps = 7 # because we took only first 7 columns (7 days)
        dataX, dataY = gen_data(ERA5_df, ERA5_df, num_steps) # dataX, dataY = gen_data(1200, 1200, 7)
        dataX = np.array(dataX, dtype=np.float32)
        dataY = np.array(dataY, dtype=np.float32)

        model = tf.keras.models.load_model("Best_Model/Whole_US/Best_Model_"+str(nearest_index)+".h5") # Load the best model
        predicted_data = model.predict(dataX)
        model_1_pred = pd.DataFrame(predicted_data)
        pred = pd.DataFrame(predicted_data)
        # Select columns 0 to 13
        pred_0_13 = pred.iloc[:, 0:14]
        # Select columns 0 to 13
        ERA5_df_0_13 = ERA5_df.iloc[:, 0:14]
        # Select columns 0 to 13
        H2OSOI_df_0_13 = H2OSOI_df.iloc[:, 0:14]
        # Find the length of the shortest array
        min_length = min(len(pred_0_13), len(ERA5_df_0_13), len(H2OSOI_df_0_13))
        # Truncate the arrays to have the same length
        ERA5_df_0_13 = ERA5_df_0_13[:min_length]
        H2OSOI_df_0_13 = H2OSOI_df_0_13[:min_length]
        pred_0_13 = pred_0_13[:min_length]
        X = np.concatenate((H2OSOI_df_0_13.values, pred_0_13.values), axis=1)
        y = ERA5_df_0_13.values
        # Reshape X to fit GRU input shape
        X = X.reshape(X.shape[0], 1, X.shape[1])  # Reshape to (samples, time steps, features)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = tf.keras.models.load_model("Best_Model/Model_2_13/Best_Model_2_Mean_13_"+str(nearest_index)+".h5")
        y_pred_13 = model.predict(X)
        # Select columns 14 to 27
        pred_14_27 = pred.iloc[:, 14:28]
        # Select columns 0 to 13
        H2OSOI_df_14_28 = H2OSOI_df.iloc[:, 14:28]
        # Select columns 0 to 13
        ERA5_df_14_28 = ERA5_df.iloc[:, 14:28]
        # Truncate the arrays to have the same length
        ERA5_df_14_28 = ERA5_df_14_28[:min_length]
        H2OSOI_df_14_28 = H2OSOI_df_14_28[:min_length]
        pred_14_27 = pred_14_27[:min_length]
        # Combine input features into a single matrix X, and set y as the target variable
        X = np.concatenate((H2OSOI_df_14_28.values, pred_14_27.values), axis=1)
        y = ERA5_df_14_28.values

        # Reshape X to fit GRU input shape
        X = X.reshape(X.shape[0], 1, X.shape[1])  # Reshape to (samples, time steps, features)
        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Make predictions
        model = tf.keras.models.load_model("Best_Model/Model_2_27/Best_Model_2_Mean_27_"+str(nearest_index)+".h5")
        y_pred_27 = model.predict(X)
        # Select columns 28 to 45
        pred_28_45 = pred.iloc[:, 28:]
        # Select columns 0 to 13
        H2OSOI_df_28_45 = H2OSOI_df.iloc[:, 28:]
        # Select columns 0 to 13
        ERA5_df_28_45 = ERA5_df.iloc[:, 28:]
        # Truncate the arrays to have the same length
        ERA5_df_28_45 = ERA5_df_28_45[:min_length]
        H2OSOI_df_28_45 = H2OSOI_df_28_45[:min_length]
        pred_28_45 = pred_28_45[:min_length]
        # Concatenate H2OSOI_df and Pred_df along columns axis
        X = np.concatenate((H2OSOI_df_28_45.values, pred_28_45.values), axis=1)
        y = ERA5_df_28_45.values
        # Reshape X to fit GRU input shape
        X = X.reshape(X.shape[0], 1, X.shape[1])  # Reshape to (samples, time steps, features)
        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        # Make predictions
        model = tf.keras.models.load_model("Best_Model/Model_2_45/Best_Model_2_Mean_45_"+str(nearest_index)+".h5")
        y_pred_45 = model.predict(X)
        y_pred_13 = pd.DataFrame(y_pred_13)
        y_pred_27 = pd.DataFrame(y_pred_27)
        y_pred_45 = pd.DataFrame(y_pred_45)
        # Concatenate the dataframes along the columns
        combined_df = pd.concat([y_pred_13, y_pred_27, y_pred_45], axis=1)
        # Reset the column names to have continuous count
        combined_df.columns = range(combined_df.shape[1])

        
        
        def get_monday_date(df, input_date):
            # Parse the input date
            # input_date = datetime.strptime(str(input_date), "%Y-%m-%d")
            print(input_date)
            print(type(input_date))

            # Get the start date of the DataFrame
            start_date = datetime(1999, 1, 4)  # Assuming the 0th row starts on 4/1/1999

            # Calculate the number of days between the input date and the start date
            days_difference = (input_date - start_date).days

            # Calculate the number of weeks
            week_number = days_difference // 7

            # Calculate the Monday date for the given week
            monday_date = start_date + timedelta(days=week_number * 7)

            return monday_date.strftime("%Y-%m-%d"),week_number
        monday_date,week_number = get_monday_date(combined_df, input_date)
        # Date Formation
        end_46th_date = str(pd.to_datetime(monday_date)+ timedelta(days=45))
        monday_date = str(monday_date)
        print("-----------------------------------")
        print("Monday date",monday_date)
        print("-----------------------------------")
        Date = pd.date_range(start= monday_date,end= end_46th_date)
        print("end date",end_46th_date)
        Date_df = pd.DataFrame(Date)
        week_number = min(week_number, len(combined_df) - 1)
        pred = combined_df.iloc[week_number]
        ERA5_df = ERA5_df.iloc[week_number]
        H2OSOI_df = H2OSOI_df.iloc[week_number]
        model_1_pred = model_1_pred.iloc[week_number]
        Combined_df = pd.concat([Date_df,ERA5_df,H2OSOI_df,pred,model_1_pred],axis=1)
        Combined_df.columns = ['Date','ERA5','H2OSOI','predictions','Model_1_Pred']
        def anomaly_correlation_coefficient(model_data, observed_data):
            # Calculate the mean along the time axis
            model_mean = np.mean(model_data, axis=0)
            observed_mean = np.mean(observed_data, axis=0)

            # Calculate the anomalies by subtracting the mean
            model_anomalies = model_data - model_mean
            observed_anomalies = observed_data - observed_mean

            # Calculate the ACC
            numerator = np.sum(model_anomalies * observed_anomalies)
            denominator = np.sqrt(np.sum(model_anomalies**2) * np.sum(observed_anomalies**2))
            acc = numerator / denominator

            return acc
        # Calculate Mean Absolute Error (MAE)
        mae = round(mean_absolute_error(Combined_df['ERA5'], Combined_df['predictions']),2)

        # Calculate Metrics for model_2
        rmse_mod_2 = round(np.sqrt(mean_squared_error(Combined_df['ERA5'], Combined_df['predictions'])),2)
        acc_mod_2 = round(anomaly_correlation_coefficient(Combined_df['predictions'],Combined_df['ERA5']),2)

        # Calculate Metrics for model_1
        rmse_mod_1 = round(np.sqrt(mean_squared_error(Combined_df['ERA5'], Combined_df['Model_1_Pred'])),2)
        acc_mod_1 = round(anomaly_correlation_coefficient(Combined_df['Model_1_Pred'],Combined_df['ERA5']),2)

        # Calculate Metrics for CESM
        rmse_CESM = round(np.sqrt(mean_squared_error(Combined_df['ERA5'], Combined_df['H2OSOI'])),2)
        acc_CESM = round(anomaly_correlation_coefficient(Combined_df['H2OSOI'],Combined_df['ERA5']),2)

        Evaluation_metrics = {
        'model_1': {
                'RMSE': rmse_mod_1,
                'ACC': acc_mod_1
            },
        'model_2': {
                'RMSE': rmse_mod_2,
                'ACC': acc_mod_2
            },
        'CESM': {
                'RMSE': rmse_CESM,
                'ACC': acc_CESM
            },
        }
        evaluation_metrics_df = pd.DataFrame([Evaluation_metrics])
        return Combined_df,evaluation_metrics_df
        

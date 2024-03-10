import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import seaborn as sns
import plotly.express as px

jan_2023 = pd.read_csv("D:/download/data/raw data/202301-divvy-tripdata.csv")
feb_2023 = pd.read_csv("D:/download/data/raw data/202302-divvy-tripdata.csv")
mar_2023 = pd.read_csv("D:/download/data/raw data/202303-divvy-tripdata.csv")
apr_2023 = pd.read_csv("D:/download/data/raw data/202304-divvy-tripdata.csv")
may_2023 = pd.read_csv("D:/download/data/raw data/202305-divvy-tripdata.csv")
jun_2023 = pd.read_csv("D:/download/data/raw data/202306-divvy-tripdata.csv")
jul_2023 = pd.read_csv("D:/download/data/raw data/202307-divvy-tripdata.csv")
aug_2023 = pd.read_csv("D:/download/data/raw data/202308-divvy-tripdata.csv")
sep_2023 = pd.read_csv("D:/download/data/raw data/202309-divvy-tripdata.csv")
oct_2023 = pd.read_csv("D:/download/data/raw data/202310-divvy-tripdata.csv")
nov_2023 = pd.read_csv("D:/download/data/raw data/202311-divvy-tripdata.csv")
dec_2023 = pd.read_csv("D:/download/data/raw data/202312-divvy-tripdata.csv")

data = pd.concat([jan_2023,feb_2023,mar_2023,apr_2023,may_2023,
                  jun_2023,jul_2023,aug_2023,sep_2023,oct_2023,nov_2023,dec_2023],
                 ignore_index = True)
data.info()
data

#Data Cleaning and Manipulating Process
#Checking the null values and counting with the sum() function
data.isna().sum()
#Dropping null values
data.dropna(inplace= True)
data.isna().sum()

# Converting datatype of "started_at" & "ended_at" columns to "datetime64" type.
data['started_at'] = pd.to_datetime(data['started_at'])
data['ended_at'] = pd.to_datetime(data['ended_at'])

data.info()

# Creating New Column "ride_length" and changing its datatype to "int32"
# In this column, each row contains the difference between "started_at and "ended_at" columns in minutes.

data['ride_length'] = (data['ended_at'] - data['started_at'])/pd.Timedelta(minutes=1)
data['ride_length'] = data['ride_length'].astype('int32')

data.head()

# Sorting Values by "ride_length" column in Ascending order.
data.sort_values(by = 'ride_length')

# Removing rows containing negative values
data = data[data['ride_length'] > 0]
data = data.reset_index()
data = data.drop(columns=['index'])
 
data

# Using the dt.day_name() to get the name of the day to each date
data["started_at"].dt.day_name()

# df['month_of_date'] = df['date_given'].dt.month
data["started_at"].dt.month

# Using the dt.month_name to see the months of each date
# later assign it into a new column
data["started_at"].dt.month_name()

# Extracting the specific day
data["started_at"].dt.day

# Now taking the year this "dt." is kind a library to manipulate date
data["started_at"].dt.year

#Create and insert new columns
data["weekday"] = data["started_at"].dt.day_name()
data["day"] = data["started_at"].dt.day
data["month"] = data["started_at"].dt.month
data["month_name"] = data["started_at"].dt.month_name()
data["year"] = data["started_at"].dt.year

data

# Checking the number of unique values for each column.
data.nunique()

# Using the duplicated() function combined with the sum() to have the total number of duplicated values
data["ride_id"].duplicated().sum()

data_cleaned = data

# df.to_csv("your_name.csv")
data_cleaned.to_csv("data_clean.csv")

#PHASE 4: ANALYZE
data_cleaned.info()

#Percentage of total users
percent = round(data_cleaned["member_casual"].value_counts(normalize = True) * 100, 1)
percent

# See the average ride length by each day for members vs casual user
data_cleaned.groupby(['member_casual','weekday']).ride_length.mean()

#fix the days of the week that are out of order.
day_order = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
data_cleaned['weekday'] = pd.Categorical(data_cleaned['weekday'], categories=day_order, ordered=True)
data_cleaned

#The average ride time by each day for members vs casual user
data_cleaned.groupby(['member_casual','weekday']).ride_length.mean()

#Analyse how casual and member use differently
data_cleaned_1 = data_cleaned.groupby('member_casual', as_index = False)['ride_length'].agg('mean')
data_cleaned_1

# Run the average ride time by each day for members vs casual users and analyze ridership data by type and weekday
data_cleaned_2 = data_cleaned.groupby(['member_casual', 'weekday'], as_index=False, observed=False)['ride_length'].agg('mean')
data_cleaned_2
# Above group by columns member_casual and weekday becomes Index of the DataFrame, In order to get these as a SQL like group by use as_index =False param or use reset_index().

# See the average ride time by each month for members vs casual user
data_cleaned_3=data_cleaned.groupby(['member_casual','month', 'month_name'], as_index=False)['ride_length'].agg('mean')
data_cleaned_3

# Count the rides, given both user, and bike type
data_cleaned_4 = data_cleaned.groupby(['member_casual','rideable_type'])['ride_id'].count().rename_axis(['member_casual', 'rideable_type']).reset_index(name = 'count')
data_cleaned_4

# no of ride by each month for members vs casual user
data_cleaned_5=data_cleaned.groupby(['member_casual','month', 'month_name'], as_index=False)['ride_id'].agg('count')
data_cleaned_5

# Visualize Percentage of Total Users
member_casual = ['member', 'casual']
fig = plt.figure(figsize =(10, 7))
plt.pie(percent, labels = member_casual, autopct = "%0.1f%%")
plt.title("Percentage of Total Users")
plt.show()

fig = plt.figure(figsize =(10, 7))
plt.pie(data_cleaned_1['ride_length'], labels = data_cleaned_1['member_casual'], autopct = "%0.1f%%")
plt.title("Average Ride Length Member vs Casual Riders in 2021")
plt.savefig('Average Ride Length Member vs Casual in 2021', dpi=300, bbox_inches='tight')
plt.show()

#visualization for average duration
fig = plt.figure(figsize =(10, 7))
sns.barplot(x='weekday', y='ride_length', hue = 'member_casual', data=data_cleaned_2)
plt.title("Average Ride Length Member vs Casual on Day of Week")
plt.xlabel("Day of Week")
plt.ylabel("Average Ride Length")
plt.savefig('Average Ride Length Member vs Casual on Day of Week.png', dpi=300)
plt.show()
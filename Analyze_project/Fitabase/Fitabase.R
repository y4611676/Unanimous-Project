install.packages("tidyverse")
install.packages("here")
install.packages("janitor")
install.packages("lubridate")
install.packages("skimr")

library(tidyverse)
library(here)
library(janitor)
library(lubridate)
library(skimr)

#Importing dataset#
sleepDay <- read_csv("D:/download/Fitabase/Raw_data/sleepDay_merged.csv")
weight <-  read_csv("D:/download/Fitabase/Raw_data/weightLogInfo_merged.csv")
dailyActivity <- read_csv("D:/download/Fitabase/Raw_data/dailyActivity_merged.csv")
hourlyCalories <- read_csv("D:/download/Fitabase/Raw_data/hourlyCalories_merged.csv")
hourlyIntensities <- read_csv("D:/download/Fitabase/Raw_data/hourlyIntensities_merged.csv")
hourlySteps <- read_csv("D:/download/Fitabase/Raw_data/hourlySteps_merged.csv")

#Look all the dataset
head(dailyActivity)
head(sleepDay)
head(weight)
head(hourlyIntensities)
head(hourlyCalories)
head(hourlySteps)

#Merging hourly_intensity, hourly_calories,hourly_steps in one single dataset
Hourly_Activity <- merge(hourlyIntensities,hourlyCalories,by=c("Id","ActivityHour"))
Hourly_Activity <- merge(Hourly_Activity,hourlySteps,by=c("Id","ActivityHour"))

#Checking the new dataset
View(Hourly_Activity)

#Checking the number of unique participant 
n_distinct(dailyActivity$Id)
n_distinct(sleepDay$Id)
n_distinct(weight$Id)
n_distinct(Hourly_Activity$Id)

#Cleaning cols names
clean_names(dailyActivity)
clean_names(sleepDay)
clean_names(Hourly_Activity)

daily_activity <- rename_with(dailyActivity,tolower)
daily_sleep <- rename_with(sleepDay,tolower)
hourly_activity <- rename_with(Hourly_Activity,tolower)

#Checking duplicates
sum(duplicated(daily_activity))
sum(duplicated(daily_sleep))
sum(duplicated(hourly_activity))

#Cleaning the 3 duplicates from daily_sleep
daily_sleep <- unique(daily_sleep)
sum(duplicated(daily_sleep))

#Converting date & time format
daily_activity$activitydate <- mdy(daily_activity$activitydate)
daily_sleep$sleepday <- mdy_hms(daily_sleep$sleepday)
hourly_activity$activityhour <- mdy_hms(hourly_activity$activityhour)

#Adding a day_of_week col to daily_activity
daily_activity$day_of_week <- wday(daily_activity$activitydate)

#Adding a total_active_hours column to daily_activity
daily_activity$total_active_hours = (daily_activity$fairlyactiveminutes + daily_activity$lightlyactiveminutes + daily_activity$sedentaryminutes + daily_activity$veryactiveminutes)/60
daily_activity$total_active_hours <- round(daily_activity$total_active_hours,2)

#Adding a total_hour_in_bed & total_hour_asleep to daily_sleep
daily_sleep$total_hour_in_bed = round((daily_sleep$totaltimeinbed)/60,2)
daily_sleep$total_hour_asleep = round((daily_sleep$totalminutesasleep)/60,2)

# Converting number of the day_of_week column to name of the day
daily_activity <- daily_activity %>% 
  mutate(day_of_week = recode(day_of_week
                              ,"1" = "Sunday"
                              ,"2" = "Monday"
                              ,"3" = "Tuesday"
                              ,"4" = "Wednesday"
                              ,"5" = "Thursday"
                              ,"6" = "Friday"
                              ,"7" = "Saturday"))

# Ordering days of weeks from Monday to Sunday 
daily_activity$day_of_week <- ordered(daily_activity$day_of_week, levels=c("Monday",
                                                                            "Tuesday",
                                                                            "Wednesday",
                                                                            "Thursday",
                                                                            "Friday",
                                                                            "Saturday",
                                                                            "Sunday"))

#Exporting the three data set for data viz in Tableau 
write.csv(daily_activity,"D:/download/Fitabase/pro_data/daily_activity.csv")
write.csv(daily_sleep,"D:/download/Fitabase/pro_data/daily_sleep.csv")
write.csv(hourly_activity,"D:/download/Fitabase/pro_data/hourly_activity.csv")
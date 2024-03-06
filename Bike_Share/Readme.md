Introduction
In this case study, I will perform tasks of a junior data analyst at a company. In order to answer the key business questions, I will follow the steps of the data analysis process: Ask, Prepare, Process, Analyze, Share, and Act.

Quick links:
Data Source: divvy_tripdata (https://divvy-tripdata.s3.amazonaws.com/index.html)

Python Data Visualization

Scenario: 

Data analyst working in the marketing analyst team at Company, a bike-share company in City. 
The director of marketing believes the company’s future success depends on maximizing the number of annual memberships. 
Therefore, team wants to understand how casual riders and annual members use Company bikes differently. 
From these insights, my team will design a new marketing strategy to convert casual riders into annual members.


Characters and teams :

A: The director of marketing and my manager. 

Marketing analytics team: A team of data analysts who are responsible for collecting, analyzing, and reporting data that helps guide Company marketing strategy. 

Executive team: The notoriously detail-oriented executive team will decide whether to approve the recommended marketing program.


About Company:

offers bike-sharing across City with over 10000 bikes at 1000 stations. They rely on flexible pricing with single-ride, day passes, and annual memberships.
Problem: While attracting customers, we want to increase annual members who are more profitable.
Solution: Convert existing casual riders to members. Casual riders already know and use, making them prime targets.
Goal: Design marketing strategies targeting casual rider conversion.
Action: Analyze historical data to understand differences between casual riders and members, motivations for membership, and digital media's impact.

Produce a report with the deliverables:

1. A clear statement of the business task : Ask
2. A description of all data sources used  : Prepare
3. Documentation of any cleaning or manipulation of data : Process
4. A summary of my analysis : Analyze
5. Supporting visualizations and key findings : Share
6. My top three recommendations based on analysis : Act


Ask process : 

Q : Identify the business task

A : To find out how casual riders and annual members use bikes differently. From these insights, would help team to design a new marketing strategy to convert casual riders into annual members.


Prepare process : 

Q: A description of all data sources used 

A : Motivate International Inc. has provided the available data. It is public data suitable for examining the usage patterns of various customer segments regarding bikes. While the data is currently disorganized, it only requires cleaning; all files are readable. It adheres to the ROCCC principles. Data Organization, Process, Combining the Data, Data Exploration,Observations, Data Cleaning, 


Process process : 

Q : Documentation of any cleaning or manipulation of data

A : Using python in Jupyter notebook helps notify and adjusting in short period of time, by running code in a line with short time, and gives out result after running saving lots of time, therefore I can check the data every now and then, and it can document every steps I take.


Analyze process : 

Q : A summary of my analysis

A : 

1. The average trip duration for the casual rider is more than that of average trip durations of the members.
2.  During summer months number of rides at its highest level for both casual and member riders.
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/d788a6a2-3320-4864-baec-101124f12091)
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/4e00f206-7709-4e95-92b6-3195e36036c0)


3. Most of the riders are member users.
4. Classic bikes are the most popular kind.
5. Only casual users use docked bikes, membership users prefer classic bikes and both of use the electric bikes almost equally.
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/ee609919-cae6-49ad-9039-65a95c994bdd)
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/03935dda-91ce-44b0-96a1-8a3e05086dce)

6. There is a seasonal trend in ridership by both casual and member riders. Can see that the rise in no of rides during summer (July to September) and during summer the casual ridership surpasses member ridership.
7. In weekends casual riders' ride length is maximum when compared to Weekdays. Members' ride length tend to be almost same in all weekdays 
8. The average ride length by casual riders is more than twice the members in the same year (2023).
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/6e8ecd04-6f64-4c95-9cc1-7086867d2c50)
![image](https://github.com/y4611676/Unanimous-Project/assets/71640831/b39ba1b5-4734-4805-88ca-3a3367158413)

Share process : 

Q : How annual members and casual riders use Company’s bikes differently?

A : 

Based on the analyze, the data can be sort in three site.
1. Trip Frequency and Duration:
Casual riders: Take fewer rides overall but their individual rides tend to be longer, especially on weekends, suggesting they use bikes for leisure or personal activities.
Annual members: Make more frequent trips, potentially indicating usage for commuting or errands. Their average trip duration is shorter, though they also use bikes for longer rides on weekends.
2. Bike Type Preference:
Casual riders: Primarily use classic bikes, possibly for their affordability and familiarity. They are the only group using docked bikes, suggesting shorter point-to-point trips.
Annual members: Prefer classic bikes but also use electric bikes nearly as much. This might indicate a mix of commuting and leisure purposes, with electric bikes chosen for efficiency or fun on some occasions.
3. Seasonality:
Both groups: Ride most frequently during summer months, aligning with leisure activities and potentially warmer weather encouraging cycling.

Act process : 

My top three recommendations based on analysis


For casual riders: 

1. Highlight the convenience and affordability of classic bikes for leisure activities.
2. Offer weekend promotions or discounts to encourage more frequent usage.
3. Consider promoting docked bikes in specific areas popular for sightseeing or recreation.

For converting casual riders to annual members: 

1. Emphasize the cost savings of an annual membership compared to frequent casual rides.
2. Showcase the versatility of classic and electric bikes for commuting, errands, and leisure.
3. Target marketing campaigns during the summer months when cycling is most popular.




### How Can a Wellness Technology Company Play It Smart?

**Data Source**: [FitBit Fitness Tracker Data](https://www.kaggle.com/datasets/arashnic/fitbit) (CC0: Public Domain, via Mobius)

---

### Scenario
1. Data analyst working at a leading manufacturer of health-focused products for women, tasked with analyzing smart device data to unearth growth opportunities.
2. The company's co-founder and Chief Creative Officer believes leveraging smart device fitness data can drive this growth.
3. Examining consumer usage patterns and deriving insights to shape the company's marketing strategy.

### Characters
- **Ur**: Co-founder and Chief Creative Officer.
- **Mur**: Co-founder and mathematician, key member of the executive team.
- **Marketing analytics team**: Responsible for collecting, analyzing, and reporting data to guide marketing strategy.

### Products
- **App**: Provides users with health data on activity, sleep, stress, menstrual cycle, and mindfulness habits.
- **Leaf**: Classic wellness tracker worn as a bracelet, necklace, or clip — tracks activity, sleep, and stress.
- **Time**: Wellness watch combining a classic timepiece with smart technology to track activity, sleep, and stress.
- **Spring**: Water bottle that tracks daily water intake using smart technology.
- **Membership**: Subscription-based program providing personalized guidance on nutrition, activity, sleep, and mindfulness.

### About the Company
Founded by Ur and Mur, the company is a high-tech firm specializing in health-focused smart products. By leveraging data collection on activity, sleep, stress, and reproductive health, it empowers women with insights into their health and habits.

---

### Deliverables
1. A clear statement of the business task — **Ask**
2. A description of all data sources used — **Prepare**
3. Documentation of any cleaning or manipulation of data — **Process**
4. A summary of analysis — **Analyze**
5. Supporting visualizations and key findings — **Share**
6. Top three recommendations based on analysis — **Act**

---

### Ask
**Business Task**:
1. What are some trends in smart device usage?
2. How could these trends apply to customers?
3. How could these trends help influence the marketing strategy?

---

### Prepare
**Data Sources**:
The primary data source is the FitBit Fitness Tracker Data, available under CC0: Public Domain and accessible through Mobius. It encompasses personal fitness tracker information from 30 Fitbit users who consented to submit their data.

**ROCCC Assessment**:
1. **Reliability**: LOW — dataset collected from 30 individuals of unknown gender.
2. **Originality**: LOW — third-party data collected via Amazon Mechanical Turk.
3. **Comprehensive**: MEDIUM — contains fields on daily activity intensity, calories, steps, sleep time, and weight.
4. **Current**: MEDIUM — data is a few years old, but lifestyle habits change slowly.
5. **Cited**: HIGH — data collector and source are well documented.

---

### Process
**Data Cleaning**:
Used R in Visual Studio to record and archive the results of each step. A complete network disconnect and archive was performed at project completion for future reference.

---

### Analyze

**Steps vs. Calories Burned**:
Positive correlation between steps taken and calories burned — the more active the user, the more calories burned.
![Steps vs Calories](https://github.com/y4611676/Unanimous-Project/assets/71640831/e9b7ba17-c270-490c-95c4-03850083cfab)

**Sleep Hours vs. Time in Bed**:
Strong positive correlation. Users who want to improve well-being should focus on increasing total time in bed.
![Sleep vs Bed Time](https://github.com/y4611676/Unanimous-Project/assets/71640831/c6bbde99-ef6a-45c1-be81-9a216178b9d1)

**Activity Levels by Day of Week**:
Sedentary activity dominates across all days with no significant variation by weekday.
![Activity by Day](https://github.com/y4611676/Unanimous-Project/assets/71640831/51fa8fd9-9710-490a-a7ac-ccec9db2ac1b)

**Average Steps per Weekday**:
Weekends and Wednesdays show a slight increase compared to other days, likely due to non-working schedules.
![Steps per Weekday](https://github.com/y4611676/Unanimous-Project/assets/71640831/a1da9e86-94de-4a52-8554-d756e74fc85d)

**Peak Activity Hours**:
Most active hours are 5–7 PM (after work) and around 12 PM (lunch break).
![Peak Hours](https://github.com/y4611676/Unanimous-Project/assets/71640831/93af6136-b0cc-41e7-add5-c58e90c69474)

---

### Share
**Smart Device Usage Trends**:
- Peak activity hours: 5–7 PM and 12 PM.
- Slight activity increase on weekends and Wednesdays.
- No significant differences in activity levels on other weekdays.

**Marketing Strategy Implications**:
- Tailor push notifications and marketing to peak activity hours.
- Consider non-working day promotions.
- Optimize campaigns based on observed usage trends.

---

### Act
**Top Recommendations**:
1. Set reminders during peak activity hours to engage users in physical exercise if calorie goals are unmet.
2. Record average wake-up times to recommend optimal bedtimes for better rest.
3. Create varied activity programs to suit different schedules and preferences.
4. Gamify usage to incentivize goal achievement and promote engagement.
5. Use data-driven insights to continuously optimize marketing initiatives.

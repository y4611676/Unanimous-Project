Topic: How Does a Bike-Share Navigate Speedy Success?

標題：共享單車如何成功?

Data Source(資料來源): divvy_tripdata (https://divvy-tripdata.s3.amazonaws.com/index.html)

Introduction: follow the steps of the data analysis process: ask, prepare, process, analyze, share, and act. 

導言：遵循資料分析流程的步驟：詢問、準備、處理、分析、分享和行動。

Scenario: 

- Data analyst working in the marketing analyst team at Company, a bike-share company in City. 
- The director of marketing believes the company’s future success depends on maximizing the number of annual memberships. 
- Therefore, team wants to understand how casual riders and annual members use Company bikes differently. 
- From these insights, my team will design a new marketing strategy to convert casual riders into annual members.

場景：

- 資料分析師在本市一家共享單車公司的行銷分析團隊工作。
- 行銷總監認為公司未來的成功取決於會員數的最大化。
- 因此，團隊希望了解休閒騎行者和會員使用公司自行車的不同方式。
- 根據這些意見，我的團隊將設計一種新的策略行銷，將散客轉變為會員。


Characters and teams :

A: The director of marketing and my manager. 

Marketing analytics team: A team of data analysts who are responsible for collecting, analyzing, and reporting data that helps guide Company marketing strategy. 

Executive team: The notoriously detail-oriented executive team will decide whether to approve the recommended marketing program.

角色與團隊：

A：行銷總監和我的經理。

行銷分析團隊：負責收集、分析和報告有助於指導公司行銷策略的數據。

執行團隊：以注重細節著稱的執行團隊將決定是否批准建議的行銷計畫。

About Company:

- offers bike-sharing across City with over 10000 bikes at 1000 stations. They rely on flexible pricing with single-ride, day passes, and annual memberships.
- Problem: While attracting customers, we want to increase annual members who are more profitable.
- Solution: Convert existing casual riders to members. Casual riders already know and use, making them prime targets.
- Goal: Design marketing strategies targeting casual rider conversion.
- Action: Analyze historical data to understand differences between casual riders and members, motivations for membership, and digital media's impact.

公司介紹：

- 共享單車：在全市 1000 個站點提供10000多輛共享單車。他們依靠單次騎行、日票和年度會員等靈活的定價方式。
- 問題：在吸引顧客的同時，我們希望增加年費會員，因為年費會員的利潤更高。
- 解決方案：將現有的散客轉化為會員。散客已經知道並了解如何使用產品，因此他們是首要目標。
- 目標：設計針對散客轉換的行銷策略。
- 行動： 分析歷史數據，了解散客與會員之間的差異、成為會員的動機、數位媒體的影響。

Produce a report with the deliverables:

1. A clear statement of the business task : Ask
2. A description of all data sources used  : Prepare
3. Documentation of any cleaning or manipulation of data : Process
4. A summary of my analysis : Analyze
5. Supporting visualizations and key findings : Share
6. My top three recommendations based on analysis : Act

編寫一份可交付的報告：

1. 明確說明業務任務：詢問
2. 所使用的所有資料來源的描述：準備
3. 對資料進行任何清理或處理的記錄： 處理
4. 我的分析摘要：分析
5. 輔助視覺化和主要發現：分享
6. 基於分析的三大建議：行動

Ask process : 

Q : Identify the business task

A : To find out how casual riders and annual members use bikes differently. From these insights, would help team to design a new marketing strategy to convert casual riders into annual members.

詢問階段：

問：確定業務任務

答：尋找散客和會員使用自行車的不同方式。從這些洞察中，幫助團隊設計新的行銷策略，將散客轉化為會員。

Prepare process : 

Q: A description of all data sources used 

A : 
- The data is public data that can use to explore how different customer types are using bikes.
- Data are disorganized, but only needs to be cleaned, all the file are readable. It’s ROCCC.

準備階段：

問: 所有資料來源的說明

答:
- 這些數據屬於公開數據，可用於探索不同客戶類型如何使用自行車。
- 資料只需清理，文件皆標明出處。符合ROCCC規範。


Process process : 

Q : Documentation of any cleaning or manipulation of data

A : Using python in Jupyter notebook helps notify and adjusting in short period of time, by running code in a line with short time, and gives out result after running saving lots of time, therefore I can check the data every now and then, and it can document every steps I take.

處理階段：

問: 任何資料清理或處理的記錄

答: 在Jupyter Notebook中使用python有助於在短時間內通知和調整，透過在短時間內運行數行程式碼，並在運行後給出結果，節省了大量時間，因此我可以時不時地查看數據，並且可以記錄我採取的每一個步驟。

Analyze process(分析階段): Summary analysis(分析摘要)

- The average trip duration for the casual rider is less than that of average trip durations of the members. 
- During summer months number of rides at its highest level for both casual and member riders.

- 散客的平均騎乘時間比會員的平均騎乘時間少。
- 夏季，散客和會員的旅行次數都達到了最高水準。
![Average Ride Length Member vs Casual in 2023](https://github.com/y4611676/Unanimous-Project/assets/71640831/37781537-3986-41c1-ac0b-a8a9b6e4d295)
![Average Ride Length Member vs Casual on Month of Year](https://github.com/y4611676/Unanimous-Project/assets/71640831/6586edcf-f4ac-4d19-ad28-91883cd14cc6)
![2023年會員與臨時使用者的平均騎行時長](https://github.com/y4611676/Unanimous-Project/assets/71640831/abeb19bf-3400-4134-af01-b366290224bc)
![會員類別與月份的平均騎行時長](https://github.com/y4611676/Unanimous-Project/assets/71640831/22bce1a5-4911-4bc1-a9ed-9aadeaf966de)



- Most of the riders are member users.
- Classic bikes are the most popular kind.
- Only casual users use docked bikes, membership users prefer classic bikes, While the number of e-bikes used by members is almost double the number used by casual visitors.

- 大多數騎乘者都是會員。
- 最受歡迎的經典自行車。
- 只有散客使用無樁電動自行車，會員更喜歡經典自行車，而會員使用電動自行車數幾乎是散客使用數的兩倍。
![Percentage of Total Users](https://github.com/y4611676/Unanimous-Project/assets/71640831/28ec9153-8b3c-4722-a365-bc4d6ac31ad2)
![Rideable types compare to riders](https://github.com/y4611676/Unanimous-Project/assets/71640831/376a918b-bf82-47e7-95e5-7eeffb742619)
![佔總用戶的百分比](https://github.com/y4611676/Unanimous-Project/assets/71640831/7f9f61cb-6470-41ad-86b2-95bf7b8d61ae)
![會員類別與騎乘類型的騎乘次數](https://github.com/y4611676/Unanimous-Project/assets/71640831/89b34de3-0d78-4424-acf7-f2092503d91b)


- There is a seasonal trend in ridership by both casual and member riders. Can see that the rise in no of rides during summer (July to September) 
- Member ridership surpasses casual ridership
- In weekends casual riders' ride length is maximum when compared to Weekdays. Members' ride length tend to be almost same in all weekdays
- The average ride length by casual riders is less than half of the members in the same year (2023).

- 散客和會員乘車次數呈趨勢趨勢。可以看出，夏季（7月至9月）的乘車次數有所增加
- 會員數一直都大於散客數。
- 與平日相比，週末散客的乘車時長較長。而會員在所有工作日的乘車時長幾乎相同。
- 同年（2023年），會員平均乘車時間是散客的兩倍以上。
![Average Ride Length Member vs Casual on Day of Week](https://github.com/y4611676/Unanimous-Project/assets/71640831/53f704ce-b588-4baf-bdec-722ed4f5b359)
![Monthly Ridership](https://github.com/y4611676/Unanimous-Project/assets/71640831/e2abff2f-ea5c-40b4-861a-3e78f4c755a3)
![騎行日與會員類型的平均騎行時長](https://github.com/y4611676/Unanimous-Project/assets/71640831/b189aaf5-ef30-4be3-b275-b5f4d2c84634)
![每月各會員類別的騎乘次數](https://github.com/y4611676/Unanimous-Project/assets/71640831/f60944c9-19f1-4451-be3d-40fed43590e0)


Share process : 

Q : How annual members and casual riders use Company’s bikes differently?

A : 

Based on the analyze, the data can be sort in three site.
1. Trip Frequency and Duration:
- Casual riders: Take fewer rides overall but their individual rides tend to be longer, especially on weekends, suggesting they use bikes for leisure or personal activities.
- Annual members: Make more frequent trips, potentially indicating usage for commuting or errands. Their average trip duration is shorter, though they also use bikes for longer rides on weekends.

2. Bike Type Preference:
- Casual riders: Primarily use classic bikes, possibly for their affordability and familiarity. They are the only group using docked bikes, suggesting shorter point-to-point trips.
- Annual members: Prefer classic bikes but also use electric bikes nearly as much. This might indicate a mix of commuting and leisure purposes, with electric bikes chosen for efficiency or fun on some occasions.

3. Seasonality: Both groups: Ride most frequently during summer months, aligning with leisure activities and potentially warmer weather encouraging cycling.

分享階段：

問: 
年度會員和散客使用公司自行車的方式有何不同？

答:
1. 旅行頻率和時間：
- 散客：整體騎乘次數較少，但單次騎乘時間往往較長，尤其是在週末，這表示他們使用自行車進行休閒或個人活動。
- 年度會員：騎乘次數較多，這可能表示他們將自行車用於通勤或差事。他們的平均騎行時間較短，但週末騎行時間也較長。

2. 自行車類型偏好：
- 散客：主要使用老式自行車，可能是因為價格低廉和熟悉。他們是唯一使用有樁自行車的群體，這表明他們的點到點騎行距離較短。
- 年度會員：喜歡經典自行車，但也幾乎同樣使用電動自行車。這可能表明他們將通勤和休閒目的結合在一起，在某些情況下選擇電動自行車是為了提高效率或增加樂趣。

3. 季節性：兩組人都是在吻夏季騎車的頻率最高，這與休閒活動和可能更溫暖的天氣相合。

Act process : Recommendations

For casual riders: 

1. Highlight the convenience and affordability of classic bikes for leisure activities.
2. Offer weekend promotions or discounts to encourage more frequent usage.
3. Consider promoting docked bikes in specific areas popular for sightseeing or recreation.

For converting casual riders to annual members: 

1. Emphasize the cost savings of an annual membership compared to frequent casual rides.
2. Showcase the versatility of classic and electric bikes for commuting, errands, and leisure.
3. Target marketing campaigns during the summer months when cycling is most popular.

行動階段：建議

針對散客：
- 突顯經典自行車在休閒活動中的便利性和經濟性。
- 提供週末促銷或折扣，鼓勵更多的人使用。
- 考慮在觀光或休閒的熱門地區推廣。

將散客轉變為年度會員：
- 告知高頻率使用的散客，年度會員可以節省成本。
- 展示經典自行車和電動自行車在通勤、差事和休閒方面的多功能性。
- 在自行車運動最受歡迎的夏季進行有針對性的行銷活動。




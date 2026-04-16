# Who Are Your Most Profitable Customers, and How Do You Turn Pay-Per-Use Into Subscribers?

An analysis of a bike-share company's 2023 data — 10,000+ bikes, 1,000+ stations — that pinpointed **exactly when, where, and how to convert casual riders into annual members.**

## This analysis is for you if:

- You run a business with two tiers (free/paid, pay-per-use/subscription, lite/pro) and conversion between them feels like a black box
- You're spending marketing budget on broad promotions and can't tell what's actually working
- You suspect your casual users and loyal users are completely different audiences, but you don't have proof

---

## What We Found (And How to Act On It)

The two customer groups behave like they're using completely different products. Once you see the gap, the marketing plan writes itself.

### Finding 1: Casual riders ride 2× longer than members

On weekends, casual riders average **28 minutes per trip** vs. **14 minutes for members.** Casual riders are doing leisure. Members are commuting.

**What to do:** Stop selling membership as "ride more, save money." That pitch doesn't match leisure users' mental model. Sell it as "your weekend ritual, cheaper" — because that's what the data says they're actually buying.

### Finding 2: Only casual riders use docked bikes — 18% of their rides

Members essentially never touch docked bikes. Members use electric bikes twice as often as casuals.

**What to do:** Docked bikes are a conversion touchpoint. Put "Members save $X on this ride" signage at docking stations in tourist and park areas. You know exactly who's standing there — someone you haven't converted yet.

### Finding 3: Both groups peak in summer (Jun–Aug) and 5–7 PM weekdays

Both groups ride on the same schedule — the marketing window is narrow and predictable.

**What to do:**
- Run annual-plan promos in **May–June** (just before peak season, when commitment to ride more is highest)
- Highlight the **8–10 ride break-even point** to casuals who've crossed their 5th ride this month (trigger it in-app)
- Skip paid marketing in January–February — the return is too low

---

## What You Get

Clear separation of two audiences and a prioritized conversion playbook:

| Output | Decision It Supports |
|--------|---------------------|
| Side-by-side behavior comparison (duration, frequency, bike choice) | Does your "upgrade" pitch match how the target actually uses your product? |
| Seasonal and hourly demand curves | When to run campaigns, when to stop spending |
| Bike-type preferences by segment | Product and pricing decisions (which SKUs to feature, which to retire) |
| Three ranked conversion strategies | What to test next quarter |

Full report: [`Bike_Share_Analysis.pdf`](./Bike_Share_Analysis.pdf)

---

## Want the Same Analysis on Your Data?

The core question — "why do some customers stay cheap and others upgrade?" — applies far beyond bike-share. Streaming services, gym chains, coworking spaces, any freemium product, any platform with usage-based pricing.

**What we need from you:**
- User-level usage logs (sessions, transactions, engagement events — whatever you track)
- Tier/subscription records (who's on which plan, when they switched)
- Basic context about your pricing tiers

**What you get back:**
- Clear behavioral differences between your tiers (not just "members use it more")
- Specific *moments* in user journeys where conversion is most likely
- A ranked list of conversion campaigns to test, with predicted lift

Reach out through the portfolio main page.

---

## For Technical Readers

Standalone analysis project using publicly available bike-share data.

### Data Source

[divvy_tripdata](https://divvy-tripdata.s3.amazonaws.com/index.html) — 2023 full year, 10,000+ bikes across 1,000+ stations.

### Approach

- **Tools**: Python, DuckDB (SQL-based aggregation), Jupyter Notebook
- **Framework**: Follows the Google Data Analytics Ask → Prepare → Process → Analyze → Share → Act structure
- **ROCCC assessment**: Data is Reliable, Original, Comprehensive, Current, and Cited — meets research-quality standards

### Visualizations

![Average Ride Length Member vs Casual in 2023](https://github.com/y4611676/Unanimous-Project/assets/71640831/37781537-3986-41c1-ac0b-a8a9b6e4d295)
![Average Ride Length Member vs Casual on Month of Year](https://github.com/y4611676/Unanimous-Project/assets/71640831/6586edcf-f4ac-4d19-ad28-91883cd14cc6)
![Percentage of Total Users](https://github.com/y4611676/Unanimous-Project/assets/71640831/28ec9153-8b3c-4722-a365-bc4d6ac31ad2)
![Rideable types compare to riders](https://github.com/y4611676/Unanimous-Project/assets/71640831/376a918b-bf82-47e7-95e5-7eeffb742619)
![Average Ride Length Member vs Casual on Day of Week](https://github.com/y4611676/Unanimous-Project/assets/71640831/53f704ce-b588-4baf-bdec-722ed4f5b359)
![Monthly Ridership](https://github.com/y4611676/Unanimous-Project/assets/71640831/e2abff2f-ea5c-40b4-861a-3e78f4c755a3)

### Deliverables Checklist

1. **Ask** — business task: identify usage differences that inform conversion strategy
2. **Prepare** — public data from divvy_tripdata, ROCCC-compliant
3. **Process** — cleaning and manipulation documented in notebook
4. **Analyze** — summary findings on duration, seasonality, bike preferences, peak hours
5. **Share** — visualizations above
6. **Act** — three actionable conversion recommendations

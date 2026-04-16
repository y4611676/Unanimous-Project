# When Are Your Users Actually Paying Attention, and What Are They Failing At?

An analysis of Fitbit wearable data that found **even health-conscious users spend 81% of their day sedentary and sleep 6.9 hours on average** — and identified the exact moments a wellness product can intervene to change behavior.

## This analysis is for you if:

- You have a consumer app or device and engagement metrics look "fine" on paper but users aren't hitting their goals
- You're sending push notifications at times that make sense to *you*, not to your users
- You suspect there's a gap between what your users say they want (sleep better, move more) and what they actually do — but you can't prove it to product or marketing

---

## What We Found (And How It Changes Product Decisions)

This was data from users who opted into a fitness tracker — people already motivated to be healthier. The gap between intent and reality was still enormous. That gap is your product opportunity.

### Finding 1: 81% of the day is sedentary — even for fitness users

Only 3% of the average day hits "fairly" or "very active." These users bought a device specifically to move more, and they're still sitting almost all day.

**Product implication:** The problem isn't motivation, it's **friction at the right moment.** Every sedentary hour is a chance to nudge. If your notification strategy is daily summaries, you're missing the actual decision point by hours.

### Finding 2: Sleep averages 6.9 hours — below the 7–9 hour recommendation

And there's an almost perfect correlation between time-in-bed and time-asleep. Users aren't tossing and turning. They're just **not going to bed in time.**

**Product implication:** Sleep-improvement campaigns should target the *bedtime decision*, not the sleep itself. "Wind down in 30 min" at the right evening hour beats a sleep-quality report the next morning.

### Finding 3: Clear activity peaks at 5–7 PM and 12 PM

Tuesdays average 8,125 steps; Sundays drop to 6,933. The pattern is crisp: lunch, post-work, weekday-heavy.

**Product implication:** Push notifications at 5 PM on Tuesdays have maximum context. Sunday mornings are the worst time to reach these users with activity prompts. Match your messaging schedule to their real lives, not your content calendar.

### Recommended actions for the product team

- Schedule notifications during **peak activity windows** (12 PM, 5–7 PM) instead of flat daily sends
- Build a **sleep-improvement campaign** that links wellness devices to bedtime reminders — target the bedtime decision, not the morning regret
- Gamify **hourly movement nudges** to break sedentary streaks — the issue is friction, not willpower

Full report: [`Fitabase_Wellness_Analysis.pdf`](./Fitabase_Wellness_Analysis.pdf)

---

## What You Get

A usage-pattern map that tells your product and marketing teams where to intervene:

| Output | Decision It Supports |
|--------|---------------------|
| Activity distribution (sedentary vs. active) | Is your product actually moving the behavior it promises? |
| Peak-hour heatmap | When to send notifications, launch campaigns, release features |
| Day-of-week patterns | Which days are growth days vs. retention days |
| Sleep vs. time-in-bed correlation | Where users are failing — and whether it's the right failure to solve |
| Three ranked product/marketing actions | What to ship or test next sprint |

---

## Want the Same Analysis on Your Data?

If you run a consumer app, wearable, wellness product, or any business with per-user engagement data, the same pattern-mapping applies.

**What we need from you:**
- User-level event data (sessions, actions, timestamps — at whatever granularity you collect)
- Your goal metric (is it DAU, conversion, retention, goal completion?)
- Basic product context (what do users think they're buying?)

**What you get back:**
- A clear picture of when users are actually engaged vs. when you *think* they are
- Specific behavioral gaps between stated intent and actual behavior
- A ranked list of product/marketing interventions, timed to the actual rhythm of user behavior

Reach out through the portfolio main page.

---

## For Technical Readers

### Data Source

[FitBit Fitness Tracker Data](https://www.kaggle.com/datasets/arashnic/fitbit) (CC0: Public Domain, via Mobius) — 30 Fitbit users.

### Approach

- **Tools**: R in Visual Studio
- **Framework**: Ask → Prepare → Process → Analyze → Share → Act
- **Scenario**: Analyst at a health-tech company selling wellness products to women. The product line includes an app, two wearables, a smart water bottle, and a subscription service for personalized guidance.

### ROCCC Data Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Reliability | LOW | 30 individuals of unknown gender |
| Originality | LOW | Third-party data (Amazon Mechanical Turk) |
| Comprehensive | MEDIUM | Activity intensity, calories, steps, sleep, weight |
| Current | MEDIUM | A few years old; habits change slowly |
| Cited | HIGH | Collector and source well documented |

### Key Visualizations

**Steps vs. Calories Burned** — strong positive correlation; the more active, the more calories.
![Steps vs Calories](https://github.com/y4611676/Unanimous-Project/assets/71640831/e9b7ba17-c270-490c-95c4-03850083cfab)

**Sleep Hours vs. Time in Bed** — near-perfect correlation; the bottleneck is bedtime, not sleep quality.
![Sleep vs Bed Time](https://github.com/y4611676/Unanimous-Project/assets/71640831/c6bbde99-ef6a-45c1-be81-9a216178b9d1)

**Activity Levels by Day of Week** — sedentary time dominates every day; no weekend escape.
![Activity by Day](https://github.com/y4611676/Unanimous-Project/assets/71640831/51fa8fd9-9710-490a-a7ac-ccec9db2ac1b)

**Average Steps per Weekday** — slight mid-week and weekend peaks.
![Steps per Weekday](https://github.com/y4611676/Unanimous-Project/assets/71640831/a1da9e86-94de-4a52-8554-d756e74fc85d)

**Peak Activity Hours** — 5–7 PM and 12 PM stand out clearly.
![Peak Hours](https://github.com/y4611676/Unanimous-Project/assets/71640831/93af6136-b0cc-41e7-add5-c58e90c69474)

### Deliverables Checklist

1. **Ask** — business task: find smart-device usage trends that inform marketing strategy
2. **Prepare** — Fitbit data, CC0 licensed, documented above
3. **Process** — data cleaning in R, archived for reproducibility
4. **Analyze** — activity patterns, sleep, time-of-day breakdown
5. **Share** — visualizations above
6. **Act** — ranked recommendations for notification timing, campaign design, and gamification

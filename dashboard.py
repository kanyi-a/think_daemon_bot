import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

LOG_FILE = "bot_monitor.log"

st.set_page_config(page_title="Bot Monitor Dashboard", layout="wide")
st.title("🤖 Bot Monitoring Dashboard")

# -----------------------------
# STEP 4.1: Parse the log file
# -----------------------------
def parse_log():
    records = []

    with open(LOG_FILE, "r") as file:
        for line in file:
            # OK responses
            ok = re.search(r"✅ (\w+) OK \(([\d.]+)s\)", line)
            if ok:
                records.append({
                    "bot": ok.group(1),
                    "status": "OK",
                    "latency": float(ok.group(2))
                })
                continue

            # BAD responses
            bad = re.search(r"⚠️ (\w+) BAD RESPONSE", line)
            if bad:
                records.append({
                    "bot": bad.group(1),
                    "status": "BAD",
                    "latency": None
                })
                continue

            # Errors
            err = re.search(r"❌ (\w+) ERROR", line)
            if err:
                records.append({
                    "bot": err.group(1),
                    "status": "ERROR",
                    "latency": None
                })

    return pd.DataFrame(records)

df = parse_log()

if df.empty:
    st.warning("No data found in bot_monitor.log")
    st.stop()

# -----------------------------
# STEP 4.2: Calculate stats
# -----------------------------
stats = df.groupby("bot").agg(
    total_checks=("status", "count"),
    ok_count=("status", lambda x: (x == "OK").sum()),
    fail_count=("status", lambda x: (x != "OK").sum()),
    avg_latency=("latency", "mean"),
    max_latency=("latency", "max"),
    min_latency=("latency", "min")
).reset_index()

stats["uptime (%)"] = (stats["ok_count"] / stats["total_checks"]) * 100

# -----------------------------
# STEP 5: Show table
# -----------------------------
st.subheader("📊 Bot Statistics")
st.dataframe(stats, use_container_width=True)

# -----------------------------
# STEP 6: Speed bar chart
# -----------------------------
st.subheader("⚡ Average Response Time (seconds)")
st.bar_chart(stats.set_index("bot")["avg_latency"])

# -----------------------------
# STEP 7: Overall health pie chart
# -----------------------------
st.subheader("🟢 Overall Bot Health")

status_counts = df["status"].value_counts()

fig, ax = plt.subplots()
ax.pie(
    status_counts,
    labels=status_counts.index,
    autopct="%1.1f%%",
    startangle=90
)
ax.axis("equal")
st.pyplot(fig)

# -----------------------------
# STEP 8: Per-bot breakdown
# -----------------------------
st.subheader("📈 Per-Bot Status Breakdown")

for bot in stats["bot"]:
    bot_data = df[df["bot"] == bot]
    counts = bot_data["status"].value_counts()

    col1, col2 = st.columns(2)

    with col1:
        uptime = stats.loc[stats.bot == bot, "uptime (%)"].values[0]
        st.metric(f"{bot} Uptime", f"{uptime:.1f}%")

    with col2:
        st.bar_chart(counts)

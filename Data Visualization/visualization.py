import boto3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import plotly.express as px
import webbrowser
from datetime import datetime

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('energy_data')

# Fetch records from DynamoDB
def fetch_records(limit=500):
    response = table.scan(Limit=limit)
    records = response['Items']
    while 'LastEvaluatedKey' in response and len(records) < limit:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'], Limit=limit - len(records))
        records.extend(response['Items'])
    return records[:limit]

# Load and preprocess data
df = pd.json_normalize(fetch_records())
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
df["energy_generated_kwh"] = pd.to_numeric(df["energy_generated_kwh"], errors='coerce')
df["energy_consumed_kwh"] = pd.to_numeric(df["energy_consumed_kwh"], errors='coerce')
df['anomaly'] = df['anomaly'].astype(bool)
df['site_id'] = df['site_id'].astype(str)
df.dropna(subset=['timestamp', 'energy_generated_kwh', 'energy_consumed_kwh'], inplace=True)

# 1. Energy Generated vs Consumed per Site
summary = df.groupby("site_id")[["energy_generated_kwh", "energy_consumed_kwh"]].sum().reset_index()
fig1, ax1 = plt.subplots(figsize=(10, 6))
bar_width = 0.35
index = range(len(summary))
ax1.bar(index, summary["energy_generated_kwh"], bar_width, label="Generated", color="gray")
ax1.bar([i + bar_width for i in index], summary["energy_consumed_kwh"], bar_width, label="Consumed", color="salmon")
ax1.set_xlabel("Site ID")
ax1.set_ylabel("Total Energy (kWh)")
ax1.set_title("Energy Generated vs Consumed per Site")
ax1.set_xticks([i + bar_width / 2 for i in index])
ax1.set_xticklabels(summary["site_id"], rotation=45)
ax1.legend()
plt.tight_layout()
plt.show()

# 2. Energy Trends Over Time
trend_df = df[(df['timestamp'] >= pd.to_datetime("2025-06-06", utc=True)) &
              (df['timestamp'] < pd.to_datetime("2025-06-08", utc=True))]
trend_df = trend_df.sort_values("timestamp")
trend = trend_df.groupby("timestamp")[["energy_generated_kwh", "energy_consumed_kwh"]].sum().reset_index()
plt.figure(figsize=(12, 6))
plt.plot(trend["timestamp"], trend["energy_generated_kwh"], label="Generated", color="green")
plt.plot(trend["timestamp"], trend["energy_consumed_kwh"], label="Consumed", color="red")
plt.xlabel("Timestamp")
plt.ylabel("Energy (kWh)")
plt.title("Energy Trends Over Time")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 3. Anomaly Rate by Site
site_counts = df.groupby('site_id').size()
anomaly_counts = df[df['anomaly']].groupby('site_id').size()
anomaly_rate = (anomaly_counts / site_counts * 100).fillna(0)
plt.figure(figsize=(10, 6))
sns.barplot(x=anomaly_rate.index, y=anomaly_rate.values, palette='viridis')
plt.title("Anomaly Rate by Site")
plt.ylabel("Anomaly Rate (%)")
plt.xlabel("Site")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())
for i, val in enumerate(anomaly_rate.values):
    plt.text(i, val + 1, f"{val:.1f}%", ha='center')
plt.ylim(0, anomaly_rate.max() + 5)
plt.tight_layout()
plt.show()

# 4. Net Energy Over Time
fig = px.scatter(
    df,
    x='timestamp',
    y='net_energy_kwh',
    color='anomaly',
    symbol='site_id',
    title='Net Energy Over Time',
    labels={'timestamp': 'Timestamp', 'net_energy_kwh': 'Net Energy (kWh)'},
    template='plotly_dark'
)
fig.write_html("net_energy_over_time.html")
import webbrowser
webbrowser.open("net_energy_over_time.html")

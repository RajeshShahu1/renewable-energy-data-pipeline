import json
import random
import time
from datetime import datetime, timezone
import boto3

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = 'renewable-energy-data1'  

# Fictitous energy site names
energy_sites = [
    "SolarFarm_AZ_001",
    "WindPark_CA_002",
    "HydroStation_OR_003",
    "GeoPlant_NV_004",
    "BatteryBank_TX_005"
]

# Function to create one energy record
def generate_record():
    site_id = random.choice(energy_sites)
    return {
        "site_id": site_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "energy_generated_kwh": round(random.uniform(-10.0, 150.0), 2),
        "energy_consumed_kwh": round(random.uniform(-10.0, 120.0), 2)
    }

# Function to generate and upload JSON to S3
def upload_data():
    records = [generate_record() for _ in range(10)]  # 10 records per file
    filename = f"energy_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    body = json.dumps(records)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=body,
        ContentType='application/json'
    )

    print(f"[✓] Uploaded file: {filename} with {len(records)} records")

# Loop every 5 minutes
# Data will be Generated and uploaded to S3 every 5 minutes
if __name__ == "__main__":
    while True:
        upload_data()
        time.sleep(300)  # 5 minutes

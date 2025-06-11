from fastapi import FastAPI, Query
from typing import Optional
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging
import json
import uvicorn

app = FastAPI(title="Energy Data API")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("energy_api")

# AWS Clients
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
sns = boto3.client('sns', region_name='us-west-2')

# Timestamp parser
def parse_ts(ts: str) -> str:
    return datetime.fromisoformat(ts).isoformat()

# Fetch records
@app.get("/records")
def get_site_records(
    site_id: str = Query(...),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    try:
        key_expr = Key("site_id").eq(site_id)
        if start_time and end_time:
            key_expr &= Key("timestamp").between(parse_ts(start_time), parse_ts(end_time))

        response = table.query(KeyConditionExpression=key_expr)
        return {"count": len(response["Items"]), "records": response["Items"]}
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch records: {e}")            # Error handling
        return {"error": str(e)}

# Anomaly endpoint
@app.get("/anomalies")
def get_anomalies(site_id: str = Query(...)):
    try:
        response = table.query(
            KeyConditionExpression=Key("site_id").eq(site_id),
            FilterExpression=Attr("anomaly").eq(True)
        )

        anomalies = response['Items']
        count = len(anomalies)
        logger.info(f"Found {count} anomalies for site {site_id}")

        return {"count": count, "anomalies": anomalies}
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch anomalies: {e}")
        return {"error": str(e)}

# Run locally
if __name__ == "__main__":
    uvicorn.run("dynamodb_api_fastapi:app", host="0.0.0.0", port=8000, reload=True)



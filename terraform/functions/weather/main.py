import functions_framework
from datetime import datetime, timedelta

import json

import requests
from google.cloud import storage
import pandas as pd


@functions_framework.http
def hello_http(request):
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    weather_url = f"https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/donnees-synop-essentielles-omm/records?where=date%20%3E%3D%20%22{date}%22&limit=100"

    print(f"Downloading data for {date}...")

    response = requests.get(weather_url)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket("weather-christophe")
    blob = bucket.blob(f"{date}.parquet")

    df = pd.DataFrame(response.json()["results"])
    bytes_data = df.to_parquet()

    blob.upload_from_string(bytes_data)

    return json.dumps({'status': 'ok'}), 200, {'Content-Type': 'application/json'}

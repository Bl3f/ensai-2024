import datetime
import io
import json
import os

from airflow.decorators import dag, task
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.hooks.subprocess import SubprocessHook

GCP_PROJECT_NAME = os.getenv("GCP_PROJECT_NAME")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
BIGQUERY_DATASET_NAME = os.getenv("BIGQUERY_DATASET_NAME")


def extract_and_load_to_gcs(url, name, ds=None):
    hook = SubprocessHook()
    folder = f"/tmp/download_{name}/{GCS_BUCKET_NAME}"
    filename = f"{folder}/{name}.csv"
    hook.run_command(command=["bash", "-c", f"mkdir -p {folder} && curl {url} -o {filename}"])

    gcs_hook = GCSHook(gcp_conn_id="bigquery")
    gcs_hook.upload(
        bucket_name=GCS_BUCKET_NAME,
        object_name=f"{name}/{ds}.csv",
        filename=filename,
    )

    hook.run_command(command=["rm", "-rf", folder])


@dag(start_date=datetime.datetime(2024, 1, 1), schedule="@weekly")
def extract_and_load_energy_data():
    data = [
        {"name": "prices", "url": "https://www.cre.fr/content/download/21061/269176"},
        {"name": "production", "url": "https://www.data.gouv.fr/fr/datasets/r/2705de2e-2a6c-4a12-bcdb-9332516993ff"},
        {"name": "consumption", "url": "https://opendata.agenceore.fr/api/explore/v2.1/catalog/datasets/conso-elec-gaz-annuelle-par-secteur-dactivite-agregee-commune/exports/csv"},
    ]

    start = DummyOperator(task_id="start")

    for config in data:
        name = config["name"]
        url = config["url"]
        extract = task(task_id=f"extract_and_load_{name}")(extract_and_load_to_gcs)(url, name)

        with open(f"dags/schema/{name}.json", "r") as f:
            schema = json.load(f)

        to_bq = GCSToBigQueryOperator(
            task_id=f"{name}_to_bq",
            gcp_conn_id="bigquery",
            bucket=GCS_BUCKET_NAME,
            source_objects=[f"{name}/{{{{ds}}}}.csv"],
            destination_project_dataset_table=f"{GCP_PROJECT_NAME}.{BIGQUERY_DATASET_NAME}.{name}",
            source_format="CSV",
            skip_leading_rows="1",
            write_disposition="WRITE_TRUNCATE",
            schema_fields=schema,
            field_delimiter=";",
            project_id=GCP_PROJECT_NAME,
        )

        start >> extract >> to_bq


extract_and_load_energy_data()

import datetime
import os

from airflow.decorators import dag, task
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator


BIGQUERY_DATASET_NAME = os.getenv("BIGQUERY_DATASET_NAME")


@dag(start_date=datetime.datetime(2023, 1, 1), schedule="@once")
def transform():
    test_query = BigQueryExecuteQueryOperator(
        task_id="test_query",
        sql="sql/test.sql",
        location="EU",
        gcp_conn_id="bigquery",
        params={"dataset": BIGQUERY_DATASET_NAME},
        destination_dataset_table=f"{BIGQUERY_DATASET_NAME}.test",
        write_disposition="WRITE_TRUNCATE",
    )


transform()

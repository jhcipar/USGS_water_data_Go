import requests
import json
import pandas as pd
import xml
import os
import pendulum

import logging

import pendulum

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
import boto3
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
 
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.environ["AWS_DATALAKE_BUCKET_NAME"]
AWS_BUCKET_REGION = os.environ.get("AWS_BUCKET_REGION")


s3 = boto3.client('s3',
    region_name=AWS_BUCKET_REGION,
    aws_access_key_id=AWS_ACCESS_KEY, 
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

task_logger = logging.getLogger('airflow.task')


def extract_raw_json(url, filetype, params):
    response = requests.get(url=url, params=params)
    # parsed = response.json()
    s3.put_object(
        Body = response.json(),
        Bucket = S3_BUCKET_NAME,
        Key = f"raw/{filetype}/{params['date']}.json"
    )



default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="extract_reddit_comment_sentiment",
    schedule_interval="@once",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["reddit_comments"],
) as dag:

    extract_reddit_sentiment_task = PythonOperator(
        task_id="extract_reddit_sentiment_task",
        python_callable=extract_raw_json,
        op_kwargs={
            'url':'https://tradestie.com/api/v1/apps/reddit',
            'filetype':'reddit_sentiment',
            'params':{
                'date':'{{ ds }}'
            }
        },
    )
    
    upload_to_s3_task = LocalFilesystemToS3Operator(
        task_id="upload_to_s3_task",
        filename="/airflow/temp/{{ ds }}_reddit_comments.csv",
        dest_key="stage/reddit_comments/",
        dest_bucket=S3_BUCKET_NAME,
        replace=True,
    )

    remove_local_file_task = BashOperator(
        task_id="remove_local_file_task",
        bash_command="rm f'/airflow/temp/{params['date']}_reddit_comments.csv'}"
    )   
    
    extract_reddit_sentiment_task >> upload_to_s3_task >> remove_local_file_task
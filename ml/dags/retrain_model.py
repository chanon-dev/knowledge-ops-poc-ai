"""Airflow DAG: Retrain model when sufficient new approved answers are available."""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/the_expert")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MIN_NEW_SAMPLES = 50
BASE_MODEL = os.getenv("BASE_MODEL", "mistralai/Mistral-7B-v0.1")

default_args = {
    "owner": "the-expert",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def check_new_data(**context):
    from training.data_pipeline import TrainingDataPipeline
    pipeline = TrainingDataPipeline()
    df = pipeline.export_approved_qa_pairs(DB_URL)
    count = len(df)
    context["ti"].xcom_push(key="sample_count", value=count)
    if count >= MIN_NEW_SAMPLES:
        return "export_data"
    return "skip_training"


def export_data(**context):
    from training.data_pipeline import TrainingDataPipeline
    pipeline = TrainingDataPipeline()
    df = pipeline.export_approved_qa_pairs(DB_URL)
    data = pipeline.convert_to_instruction_format(df)
    data = pipeline.clean_and_deduplicate(data)
    train, val, test = pipeline.split_dataset(data)
    pipeline.save_jsonl(train, "/tmp/train.jsonl")
    pipeline.save_jsonl(val, "/tmp/val.jsonl")
    pipeline.save_jsonl(test, "/tmp/test.jsonl")
    context["ti"].xcom_push(key="train_size", value=len(train))


def train_model(**context):
    import json
    from training.lora_trainer import LoRATrainer

    with open("/tmp/train.jsonl") as f:
        train_data = [json.loads(line) for line in f]
    with open("/tmp/val.jsonl") as f:
        val_data = [json.loads(line) for line in f]

    trainer = LoRATrainer()
    trainer.setup(base_model=BASE_MODEL)
    metrics = trainer.train(train_data, val_data, output_dir="/tmp/lora_output")
    trainer.save_adapter("/tmp/lora_adapter")
    context["ti"].xcom_push(key="train_metrics", value=metrics)


def evaluate_model(**context):
    import json
    from training.lora_trainer import LoRATrainer

    with open("/tmp/test.jsonl") as f:
        test_data = [json.loads(line) for line in f]

    trainer = LoRATrainer()
    trainer.setup(base_model=BASE_MODEL)
    metrics = trainer.evaluate(test_data)
    context["ti"].xcom_push(key="eval_metrics", value=metrics)

    if metrics.get("rougeL", 0) < 0.3:
        raise ValueError(f"Model quality too low: ROUGE-L={metrics['rougeL']:.3f}. Rolling back.")


def deploy_model(**context):
    from training.model_deployer import ModelDeployer
    deployer = ModelDeployer()
    deployer.register_model(MLFLOW_URI, "the-expert-lora", "latest", "/tmp/lora_adapter")
    deployer.deploy_to_ollama("/tmp/lora_adapter", "the-expert-custom")


with DAG(
    "retrain_model",
    default_args=default_args,
    description="Retrain LoRA model when enough new approved data is available",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ml", "training"],
) as dag:

    check = BranchPythonOperator(task_id="check_new_data", python_callable=check_new_data)
    skip = EmptyOperator(task_id="skip_training")
    export = PythonOperator(task_id="export_data", python_callable=export_data)
    train = PythonOperator(task_id="train_model", python_callable=train_model)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    deploy = PythonOperator(task_id="deploy_model", python_callable=deploy_model)

    check >> [export, skip]
    export >> train >> evaluate >> deploy

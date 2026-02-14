import os
import logging
from typing import Optional

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import evaluate
import mlflow

logger = logging.getLogger(__name__)


class LoRATrainer:
    """Fine-tune a language model using LoRA (Low-Rank Adaptation)."""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.peft_model = None

    def setup(
        self,
        base_model: str = "mistralai/Mistral-7B-v0.1",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[list[str]] = None,
    ):
        logger.info(f"Loading base model: {base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=target_modules or ["q_proj", "v_proj", "k_proj", "o_proj"],
        )
        self.peft_model = get_peft_model(self.model, lora_config)
        trainable = sum(p.numel() for p in self.peft_model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.peft_model.parameters())
        logger.info(f"Trainable params: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    def _tokenize(self, data: list[dict], max_length: int = 512) -> Dataset:
        texts = []
        for item in data:
            prompt = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n{item['output']}"
            texts.append(prompt)

        dataset = Dataset.from_dict({"text": texts})
        return dataset.map(
            lambda x: self.tokenizer(
                x["text"], truncation=True, max_length=max_length, padding="max_length"
            ),
            batched=True,
            remove_columns=["text"],
        )

    def train(
        self,
        train_data: list[dict],
        val_data: list[dict],
        output_dir: str = "./lora_output",
        epochs: int = 3,
        lr: float = 2e-4,
        batch_size: int = 4,
        mlflow_experiment: str = "the-expert-lora",
    ) -> dict:
        train_dataset = self._tokenize(train_data)
        val_dataset = self._tokenize(val_data)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=lr,
            warmup_steps=100,
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            fp16=torch.cuda.is_available(),
            report_to=["mlflow"],
        )

        mlflow.set_experiment(mlflow_experiment)
        with mlflow.start_run():
            mlflow.log_params({
                "epochs": epochs, "lr": lr, "batch_size": batch_size,
                "train_samples": len(train_data), "val_samples": len(val_data),
            })

            trainer = Trainer(
                model=self.peft_model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=DataCollatorForLanguageModeling(self.tokenizer, mlm=False),
            )
            result = trainer.train()
            metrics = {
                "train_loss": result.training_loss,
                "train_runtime": result.metrics.get("train_runtime", 0),
            }
            eval_result = trainer.evaluate()
            metrics["eval_loss"] = eval_result.get("eval_loss", 0)
            mlflow.log_metrics(metrics)

        return metrics

    def evaluate(self, test_data: list[dict]) -> dict:
        rouge = evaluate.load("rouge")
        bleu = evaluate.load("bleu")

        predictions, references = [], []
        for item in test_data:
            prompt = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n"
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.peft_model.device)
            with torch.no_grad():
                outputs = self.peft_model.generate(**inputs, max_new_tokens=256)
            pred = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            pred = pred.split("### Response:\n")[-1].strip()
            predictions.append(pred)
            references.append(item["output"])

        rouge_scores = rouge.compute(predictions=predictions, references=references)
        bleu_score = bleu.compute(predictions=[p.split() for p in predictions], references=[[r.split()] for r in references])

        return {
            "rouge1": rouge_scores["rouge1"],
            "rouge2": rouge_scores["rouge2"],
            "rougeL": rouge_scores["rougeL"],
            "bleu": bleu_score["bleu"],
            "num_samples": len(test_data),
        }

    def save_adapter(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        self.peft_model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        logger.info(f"LoRA adapter saved to {output_dir}")

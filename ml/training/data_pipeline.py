import json
import hashlib
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text


class TrainingDataPipeline:
    """Export approved Q&A pairs from PostgreSQL and prepare for fine-tuning."""

    def export_approved_qa_pairs(
        self, db_url: str, tenant_id: Optional[str] = None
    ) -> pd.DataFrame:
        engine = create_engine(db_url)
        query = """
            SELECT
                m_q.content AS question,
                m_a.content AS answer,
                c.department_id,
                m_a.confidence,
                m_a.created_at
            FROM messages m_q
            JOIN messages m_a ON m_a.conversation_id = m_q.conversation_id
            JOIN conversations c ON c.id = m_q.conversation_id
            LEFT JOIN approvals a ON a.message_id = m_a.id
            WHERE m_q.role = 'user'
              AND m_a.role = 'assistant'
              AND (a.status = 'approved' OR m_a.confidence >= 0.85)
        """
        params = {}
        if tenant_id:
            query += " AND c.tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id

        query += " ORDER BY m_a.created_at DESC"

        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df

    def convert_to_instruction_format(self, df: pd.DataFrame) -> list[dict]:
        records = []
        for _, row in df.iterrows():
            records.append({
                "instruction": "Answer the following question accurately based on your knowledge.",
                "input": row["question"],
                "output": row["answer"],
            })
        return records

    def clean_and_deduplicate(self, data: list[dict]) -> list[dict]:
        seen = set()
        cleaned = []
        for item in data:
            text_input = item.get("input", "").strip()
            text_output = item.get("output", "").strip()
            if not text_input or not text_output:
                continue
            key = hashlib.md5(f"{text_input}::{text_output}".encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append({
                "instruction": item["instruction"],
                "input": text_input,
                "output": text_output,
            })
        return cleaned

    def split_dataset(
        self, data: list[dict], train: float = 0.8, val: float = 0.1, test: float = 0.1
    ) -> tuple[list[dict], list[dict], list[dict]]:
        import random
        random.shuffle(data)
        n = len(data)
        train_end = int(n * train)
        val_end = train_end + int(n * val)
        return data[:train_end], data[train_end:val_end], data[val_end:]

    def save_jsonl(self, data: list[dict], path: str):
        with open(path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

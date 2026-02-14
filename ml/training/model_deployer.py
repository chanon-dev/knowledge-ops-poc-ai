import os
import subprocess
import logging
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


class ModelDeployer:
    """Export, quantize, and deploy fine-tuned models."""

    def export_onnx(self, model_path: str, output_path: str):
        from optimum.onnxruntime import ORTModelForCausalLM

        os.makedirs(output_path, exist_ok=True)
        model = ORTModelForCausalLM.from_pretrained(model_path, export=True)
        model.save_pretrained(output_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        tokenizer.save_pretrained(output_path)
        logger.info(f"ONNX model exported to {output_path}")

    def quantize(self, model_path: str, output_path: str, bits: int = 8):
        from optimum.onnxruntime import ORTQuantizer
        from optimum.onnxruntime.configuration import AutoQuantizationConfig

        os.makedirs(output_path, exist_ok=True)
        if bits == 8:
            qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False)
        else:
            qconfig = AutoQuantizationConfig.arm64(is_static=False)

        quantizer = ORTQuantizer.from_pretrained(model_path)
        quantizer.quantize(save_dir=output_path, quantization_config=qconfig)
        logger.info(f"Quantized model ({bits}-bit) saved to {output_path}")

    def register_model(self, mlflow_uri: str, model_name: str, version: str, model_path: str):
        import mlflow

        mlflow.set_tracking_uri(mlflow_uri)
        with mlflow.start_run():
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=None,
                artifacts={"model_dir": model_path},
                registered_model_name=model_name,
            )
        logger.info(f"Model {model_name} v{version} registered in MLflow")

    def deploy_to_ollama(self, model_path: str, model_name: str):
        modelfile_content = f"""FROM {model_path}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM You are The Expert, an enterprise AI assistant. Answer questions accurately based on the provided context and knowledge base.
"""
        modelfile_path = Path(model_path) / "Modelfile"
        modelfile_path.write_text(modelfile_content)

        try:
            subprocess.run(
                ["ollama", "create", model_name, "-f", str(modelfile_path)],
                check=True, capture_output=True, text=True,
            )
            logger.info(f"Model {model_name} deployed to Ollama")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy to Ollama: {e.stderr}")
            raise

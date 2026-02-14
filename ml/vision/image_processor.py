import base64
import io
import logging
from pathlib import Path

from PIL import Image
import httpx

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process images for vision-based queries."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def preprocess(self, image_path: str, max_size: int = 1024) -> str:
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def extract_text_ocr(self, image_path: str) -> str:
        try:
            import pytesseract
            img = Image.open(image_path)
            return pytesseract.image_to_string(img)
        except ImportError:
            logger.warning("pytesseract not installed, falling back to vision model")
            return ""

    async def describe_image(self, image_path: str, model: str = "llava") -> str:
        image_b64 = self.preprocess(image_path)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": "Describe this image in detail. Include any text, diagrams, charts, or relevant information visible.",
                    "images": [image_b64],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

    async def analyze_screenshot(self, image_path: str, query: str, model: str = "llava") -> str:
        ocr_text = self.extract_text_ocr(image_path)
        image_b64 = self.preprocess(image_path)

        prompt = f"""Analyze this screenshot and answer the following question:

Question: {query}

"""
        if ocr_text:
            prompt += f"OCR extracted text:\n{ocr_text}\n\n"
        prompt += "Provide a detailed answer based on what you see in the image."

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

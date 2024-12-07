import torch

from colpali_engine.models import ColQwen2, ColQwen2Processor

model = ColQwen2.from_pretrained(
    "vidore/colqwen2-v1.0",
    torch_dtype=torch.bfloat16,
    device_map="mps",  # or "mps" if on Apple Silicon
)
processor = ColQwen2Processor.from_pretrained("vidore/colqwen2-v1.0")

colpali_model = model
colpali_processor = processor

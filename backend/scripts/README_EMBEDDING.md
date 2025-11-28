# SCIN Database Embedding with SigLIP

This directory contains scripts for embedding the Harvard SCIN dermatology dataset using SigLIP (Sigmoid Loss for Language Image Pre-training).

## Why SigLIP?

SigLIP is superior to CLIP for medical image retrieval because:
- **Better fine-grained recognition**: Excels at distinguishing subtle visual differences (crucial for dermatology)
- **Efficient sigmoid loss**: More efficient training and better performance
- **Medical domain**: Better zero-shot performance on specialized domains

## Scripts

### 1. `embed_scin_siglip.py`
Main embedding script that processes SCIN images and stores embeddings in Qdrant.

**Features:**
- Batch processing for efficiency
- GPU acceleration (if available)
- Progress tracking with tqdm
- Error handling for missing images
- Preserves all metadata from CSV

### 2. `test_siglip_embedding.py`
Quick test script that processes only 10 images to verify the pipeline works.

## Quick Start

### Test the Pipeline (10 images)

```bash
cd /home/sankar/rural-medical-kiosk-ui/backend
source .venv/bin/activate
python scripts/test_siglip_embedding.py
```

### Embed All Data (~6,500 images)

```bash
cd /home/sankar/rural-medical-kiosk-ui/backend
source .venv/bin/activate
python scripts/embed_scin_siglip.py
```

### Embed Subset (e.g., 1000 images)

```bash
python scripts/embed_scin_siglip.py --limit 1000
```

## Usage Options

```bash
python scripts/embed_scin_siglip.py [OPTIONS]

Options:
  --metadata PATH        Path to real_labeled_metadata.csv
                        (default: /home/sankar/data/scin/real_labeled_metadata.csv)

  --images-dir PATH     Path to images directory
                        (default: /home/sankar/data/scin/images)

  --collection NAME     Qdrant collection name
                        (default: scin_dermatology)

  --batch-size N        Batch size for embedding
                        (default: 32)

  --limit N             Limit number of images to process
                        (useful for testing)

  --model NAME          SigLIP model to use
                        (default: google/siglip-base-patch16-224)
```

## Performance

### Expected Processing Time

- **GPU (NVIDIA RTX 3090/4090)**: ~2-3 images/second → ~30-45 minutes for full dataset
- **GPU (NVIDIA T4/V100)**: ~1-2 images/second → ~60-90 minutes
- **CPU only**: ~0.1-0.5 images/second → 3-6 hours

### Memory Requirements

- **Model**: ~500 MB
- **Batch processing (32 images)**: ~2-3 GB GPU memory
- **Total recommended**: 6+ GB GPU memory or 16+ GB RAM

## Embedding Details

### Vector Dimensions

- **SigLIP-base**: 768 dimensions
- Normalized for cosine similarity

### Metadata Stored

Each vector point includes:
- `image_id`: Unique image identifier
- `image_path`: Relative path to image
- `case_id`: Case identifier
- `condition`: Primary condition label
- `all_conditions`: List of all conditions
- `weighted_labels`: Confidence scores for each label
- `age_group`: Patient age group
- `sex_at_birth`: Patient sex
- `fitzpatrick_skin_type`: Skin type classification
- `description`: Textual description
- `split`: train/test/val split

## Querying the Database

After embedding, you can search for similar images:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Embed a query image using the same SigLIP model
query_embedding = embedder.embed_image("path/to/query.jpg")

# Search for similar images
results = client.search(
    collection_name="scin_dermatology",
    query_vector=query_embedding,
    limit=5
)

for result in results:
    print(f"Condition: {result.payload['condition']}")
    print(f"Score: {result.score}")
    print(f"Image: {result.payload['image_path']}")
```

## Troubleshooting

### CUDA Out of Memory

Reduce batch size:
```bash
python scripts/embed_scin_siglip.py --batch-size 16
```

### Model Download Issues

The script will auto-download the SigLIP model from HuggingFace. If you have connection issues, pre-download:
```bash
python -c "from transformers import AutoModel; AutoModel.from_pretrained('google/siglip-base-patch16-224')"
```

### Missing Images

The script will skip images that don't exist and continue processing. Check the output for warnings.

## Advanced: Using Different Models

### SigLIP Variants

```bash
# Larger model (better quality, slower)
python scripts/embed_scin_siglip.py --model google/siglip-large-patch16-384

# Smaller model (faster, less quality)
python scripts/embed_scin_siglip.py --model google/siglip-small-patch16-224
```

## Next Steps

After embedding:

1. **Verify embeddings**: Check Qdrant dashboard at http://localhost:6333/dashboard
2. **Test retrieval**: Use the backend API to test similarity search
3. **Fine-tune** (optional): Fine-tune SigLIP on your specific dermatology data for better performance

## References

- SigLIP Paper: https://arxiv.org/abs/2303.15343
- HuggingFace Models: https://huggingface.co/google/siglip-base-patch16-224
- Qdrant Docs: https://qdrant.tech/documentation/

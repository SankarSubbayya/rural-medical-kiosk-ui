#!/usr/bin/env python3
"""
SCIN Database Ingestion Script

This script ingests the Harvard SCIN (Skin Condition Image Network) database
into Qdrant for RAG retrieval.

Usage:
    python scripts/ingest_scin.py --data-dir /path/to/scin/data

Expected SCIN data structure:
    scin_data/
    ├── images/
    │   ├── eczema/
    │   │   ├── img_001.jpg
    │   │   └── ...
    │   ├── psoriasis/
    │   └── ...
    ├── metadata.json  # Optional: structured metadata
    └── conditions.csv # Optional: condition descriptions
"""
import asyncio
import argparse
import json
import csv
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService
from app.models.analysis import SCINRecord
from app.config import ICD_CODES


async def ingest_from_directory(
    data_dir: Path,
    rag_service: RAGService,
    batch_size: int = 100
) -> int:
    """
    Ingest SCIN data from a directory structure.

    Args:
        data_dir: Path to SCIN data directory
        rag_service: RAGService instance
        batch_size: Number of records to process before logging progress

    Returns:
        Number of records ingested
    """
    count = 0
    images_dir = data_dir / "images"

    if not images_dir.exists():
        print(f"Images directory not found: {images_dir}")
        return 0

    # Load metadata if available
    metadata = load_metadata(data_dir)
    condition_descriptions = load_condition_descriptions(data_dir)

    print(f"Scanning {images_dir}...")

    for condition_dir in sorted(images_dir.iterdir()):
        if not condition_dir.is_dir():
            continue

        condition_name = condition_dir.name.replace("_", " ").title()
        condition_key = condition_dir.name.lower()
        icd_code = ICD_CODES.get(condition_key, "L98.9")
        description = condition_descriptions.get(
            condition_key,
            f"Dermatological condition: {condition_name}"
        )

        print(f"Processing: {condition_name} (ICD-10: {icd_code})")

        image_files = list(condition_dir.glob("*.jpg")) + \
                      list(condition_dir.glob("*.jpeg")) + \
                      list(condition_dir.glob("*.png"))

        for image_file in image_files:
            # Get specific metadata for this image if available
            image_metadata = metadata.get(image_file.name, {})

            record = SCINRecord(
                id=f"scin_{condition_key}_{image_file.stem}",
                condition=condition_name,
                icd_code=icd_code,
                description=description,
                image_path=str(image_file),
                body_location=image_metadata.get("body_location"),
                skin_type=image_metadata.get("skin_type"),
                characteristics=image_metadata.get("characteristics", [])
            )

            try:
                await rag_service.add_scin_record(record)
                count += 1

                if count % 10 == 0:
                    print(f"  Processed {count} images...")

                if count % batch_size == 0:
                    print(f"  Progress: {count} records ingested")

            except Exception as e:
                print(f"  Error processing {image_file.name}: {e}")

    return count


def load_metadata(data_dir: Path) -> dict:
    """Load image metadata from JSON file if available."""
    metadata_path = data_dir / "metadata.json"

    if metadata_path.exists():
        with open(metadata_path) as f:
            data = json.load(f)
            # Convert to dict keyed by filename
            return {
                r.get("filename", r.get("image_path", "").split("/")[-1]): r
                for r in data.get("records", data.get("images", []))
            }

    return {}


def load_condition_descriptions(data_dir: Path) -> dict:
    """Load condition descriptions from CSV if available."""
    descriptions = {}

    csv_path = data_dir / "conditions.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("condition", "").lower().replace(" ", "_")
                descriptions[key] = row.get("description", "")

    # Default descriptions for common conditions
    defaults = {
        "eczema": "Eczema (atopic dermatitis) is a chronic skin condition causing dry, itchy, inflamed skin. Common in children but can affect adults. Often appears in skin folds.",
        "psoriasis": "Psoriasis is an autoimmune condition causing rapid skin cell buildup, resulting in thick, scaly patches. Often appears on elbows, knees, and scalp.",
        "acne": "Acne vulgaris is a common skin condition occurring when hair follicles become clogged with oil and dead skin cells. Causes pimples, blackheads, and whiteheads.",
        "contact_dermatitis": "Contact dermatitis is an itchy rash caused by direct contact with a substance or an allergic reaction. Common triggers include soaps, cosmetics, and plants.",
        "urticaria": "Urticaria (hives) are itchy, raised welts on the skin that appear suddenly. Usually caused by allergic reactions to food, medications, or other triggers.",
        "fungal_infection": "Fungal skin infections are caused by various fungi and can affect different body parts. Common types include ringworm, athlete's foot, and jock itch.",
        "melanoma": "Melanoma is the most serious type of skin cancer, developing in the cells that give skin its color. Warning signs include asymmetry, irregular borders, multiple colors, large diameter, and evolution.",
        "vitiligo": "Vitiligo is a condition causing loss of skin color in patches. It occurs when melanocytes (pigment-producing cells) die or stop functioning.",
        "rosacea": "Rosacea is a chronic skin condition causing redness, visible blood vessels, and sometimes small, pus-filled bumps on the face.",
        "impetigo": "Impetigo is a highly contagious bacterial skin infection causing red sores that can break open, ooze, and develop a yellow-brown crust.",
        "cellulitis": "Cellulitis is a potentially serious bacterial skin infection causing red, swollen, tender skin. Requires prompt treatment to prevent spreading.",
        "herpes_simplex": "Herpes simplex virus causes cold sores (oral herpes) or genital herpes. Appears as painful blisters that may recur periodically.",
        "herpes_zoster": "Herpes zoster (shingles) is a viral infection causing a painful rash. It's caused by reactivation of the chickenpox virus.",
        "scabies": "Scabies is an itchy skin condition caused by tiny mites that burrow into the skin. Highly contagious through close contact.",
        "tinea": "Tinea (ringworm) is a fungal infection causing ring-shaped, scaly patches on the skin. Different types affect different body areas.",
    }

    for key, desc in defaults.items():
        if key not in descriptions:
            descriptions[key] = desc

    return descriptions


async def main():
    parser = argparse.ArgumentParser(
        description="Ingest SCIN database into Qdrant"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to SCIN data directory"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for progress logging (default: 100)"
    )

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    print("=" * 60)
    print("SCIN Database Ingestion (Qdrant)")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print()

    # Initialize RAG service
    rag_service = RAGService()

    # Get initial stats
    initial_stats = rag_service.get_collection_stats()
    print(f"Initial collection stats: {initial_stats}")

    # Ingest data
    count = await ingest_from_directory(data_dir, rag_service, args.batch_size)

    # Get final stats
    final_stats = rag_service.get_collection_stats()

    print()
    print("=" * 60)
    print("Ingestion Complete")
    print("=" * 60)
    print(f"Records ingested: {count}")
    print(f"Final collection stats: {final_stats}")


if __name__ == "__main__":
    asyncio.run(main())

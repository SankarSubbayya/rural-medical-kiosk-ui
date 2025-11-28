#!/usr/bin/env python3
"""
Quick test script for SigLIP embedding on a small subset of SCIN data.

This script tests the embedding pipeline on just 10 images to verify everything works.

Usage:
    python scripts/test_siglip_embedding.py
"""
import subprocess
import sys

def main():
    print("=" * 70)
    print("Testing SigLIP Embedding on 10 SCIN Images")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Load the SigLIP model")
    print("  2. Process 10 images from the SCIN dataset")
    print("  3. Create embeddings")
    print("  4. Store them in Qdrant")
    print()

    # Run the embedding script with limit=10
    cmd = [
        sys.executable,
        "scripts/embed_scin_siglip.py",
        "--limit", "10",
        "--batch-size", "5"
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd="/home/sankar/rural-medical-kiosk-ui/backend")

    if result.returncode == 0:
        print()
        print("=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run full embedding:")
        print("     python scripts/embed_scin_siglip.py")
        print()
        print("  2. Or process specific number of images:")
        print("     python scripts/embed_scin_siglip.py --limit 1000")
    else:
        print()
        print("✗ Test failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

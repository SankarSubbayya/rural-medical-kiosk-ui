#!/usr/bin/env python3
"""
Check if all dependencies for SigLIP embedding are installed.
"""
import sys

def check_dependencies():
    """Check all required packages."""
    print("=" * 70)
    print("Checking Dependencies for SigLIP Embedding")
    print("=" * 70)
    print()

    missing = []
    installed = []

    # Required packages
    packages = {
        'torch': 'PyTorch',
        'transformers': 'HuggingFace Transformers',
        'PIL': 'Pillow (PIL)',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'tqdm': 'tqdm',
        'qdrant_client': 'Qdrant Client',
    }

    for module, name in packages.items():
        try:
            __import__(module)
            installed.append(name)
            print(f"✓ {name}")
        except ImportError:
            missing.append(name)
            print(f"✗ {name} - NOT INSTALLED")

    print()
    print("-" * 70)

    if missing:
        print(f"Missing {len(missing)} package(s):")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        print("To install missing packages:")
        print("  cd backend")
        print("  source .venv/bin/activate")
        print("  pip install torch transformers pillow pandas numpy tqdm")
        return False
    else:
        print(f"✓ All {len(installed)} required packages are installed!")
        print()

        # Check CUDA
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
                print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                print("⚠ CUDA not available - will use CPU (slower)")
        except:
            pass

        print()
        print("Ready to run embedding scripts!")
        return True

if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)

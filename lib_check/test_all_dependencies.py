# test_all_dependencies.py
print("=== Testing All Dependencies ===")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA: {torch.cuda.is_available()}")
except:
    print("❌ PyTorch issue")

try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
except:
    print("❌ Transformers issue")

try:
    import timm
    print(f"✅ timm: {timm.__version__}")
except:
    print("❌ timm issue")

try:
    from huggingface_hub import login
    print("✅ Hugging Face Hub: Ready")
except:
    print("❌ HF Hub issue")

print("\n🎉 If all show ✅, we're ready for Gemma 3n!")
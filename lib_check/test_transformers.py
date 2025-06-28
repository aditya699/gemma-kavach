# test_transformers.py
import transformers
print(f"✅ Transformers version: {transformers.__version__}")

# Check if version meets requirements
version = transformers.__version__
major, minor = version.split('.')[:2]
if int(major) >= 4 and int(minor) >= 51:
    print("✅ Version meets Gemma 3n requirements (>=4.51.3)")
else:
    print("⚠️ Version might be too old")

# Test basic import
try:
    from transformers import pipeline
    print("✅ Pipeline import successful")
except Exception as e:
    print(f"❌ Pipeline import failed: {e}")
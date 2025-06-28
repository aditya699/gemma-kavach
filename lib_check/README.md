# Lib Check - Environment Setup & Testing Scripts

This folder contains testing scripts used to setup and validate the environment for **Gemma 3n (Gemma-3n-E4B-it)** model. These scripts help ensure all dependencies are properly installed and the model is working correctly.

## 🎯 Purpose

The scripts in this folder are designed to:
- Verify all required dependencies are installed
- Test model loading and inference capabilities
- Benchmark performance and speed
- Validate different inference methods
- Test multimodal capabilities (text + image)

## 📋 Prerequisites

Before running these scripts, ensure you have:
- Python 3.8+
- CUDA-compatible GPU (recommended: RTX 4090 or similar)
- Hugging Face account with access token
- Required Python packages (see `requirements.txt` in parent directory)

## 🔧 Setup Scripts

### Core Dependency Testing

#### `test_all_dependencies.py`
**Purpose**: Comprehensive dependency checker for all required packages
```bash
python test_all_dependencies.py
```
- ✅ Tests PyTorch installation and CUDA availability
- ✅ Verifies Transformers library version
- ✅ Checks timm (image processing) library
- ✅ Validates Hugging Face Hub connectivity

#### `test_torch.py`
**Purpose**: Focused PyTorch and CUDA testing
```bash
python test_torch.py
```
- Tests PyTorch version compatibility
- Verifies CUDA availability and GPU detection
- Displays GPU information if available

#### `test_transformers.py`
**Purpose**: Transformers library validation
```bash
python test_transformers.py
```
- Checks Transformers version (requires >=4.51.3 for Gemma 3n)
- Tests pipeline import functionality
- Validates version compatibility

## 🚀 Model Testing Scripts

### Basic Model Testing

#### `test_gemma3n.py`
**Purpose**: Basic Gemma 3n model loading and inference test
```bash
python test_gemma3n.py
```
- **⚠️ Important**: Replace `HF_TOKEN = "please get it from portal"` with your actual Hugging Face token
- Downloads model (~5GB on first run)
- Tests basic text generation
- Validates model functionality

### Performance & Speed Testing

#### `speed_text.py`
**Purpose**: Compares different text generation methods for performance
```bash
python speed_text.py
```
- **⚠️ Important**: Update HF token before running
- Compares "our method" vs "their method" approaches
- Benchmarks inference speed
- Provides detailed performance metrics

#### `debugspeed.py`
**Purpose**: Optimized inference with compilation issues resolved
```bash
python debugspeed.py
```
- **⚠️ Important**: Update HF token before running
- Disables PyTorch graph optimizations for stability
- Tests streaming text generation
- Provides tokens-per-second metrics

#### `optgemma3n.py`
**Purpose**: Fast inference optimization testing
```bash
python optgemma3n.py
```
- Optimized settings for RTX 4090
- Uses bfloat16 precision for speed
- Includes warm-up runs for accurate benchmarking
- Reports generation speed in tokens/second

#### `textgen3n.py`
**Purpose**: Optimized text generation with various configurations
```bash
python textgen3n.py
```
- **⚠️ Important**: Update HF token before running
- Tests both short and normal generation lengths
- Uses optimized PyTorch settings
- Benchmarks loading and generation times

## 🖼️ Multimodal Testing

#### `image_test.py`
**Purpose**: Tests Gemma 3n's vision capabilities (image + text)
```bash
python image_test.py
```
- Downloads and processes test image
- Tests image-to-text generation
- Uses official Google approach for multimodal inference
- Measures processing time for vision tasks

## 🔄 Alternative Inference Methods

#### `ollama_serve.py`
**Purpose**: Tests Ollama-based inference (alternative to direct Transformers)
```bash
python ollama_serve.py
```
- **Prerequisites**: Ollama must be installed and `gemma3n` model pulled
- Tests streaming generation via Ollama
- Compares performance with direct Transformers approach
- Provides words-per-second metrics

## 📝 Usage Instructions

### 1. Initial Setup
```bash
# Run dependency check first
python test_all_dependencies.py

# If all dependencies pass, test basic functionality
python test_torch.py
python test_transformers.py
```

### 2. Model Testing
```bash
# Test basic model loading (update HF token first!)
python test_gemma3n.py

# Test optimized inference
python optgemma3n.py
```

### 3. Performance Benchmarking
```bash
# Compare different methods
python speed_text.py

# Test streaming and optimizations
python debugspeed.py
python textgen3n.py
```

### 4. Multimodal Testing
```bash
# Test vision capabilities
python image_test.py
```

## ⚠️ Important Notes

1. **Hugging Face Token**: Most scripts require a valid HF token. Replace `"please get it from portal"` with your actual token from [Hugging Face Settings](https://huggingface.co/settings/tokens)

2. **Model Access**: Ensure you have access to `google/gemma-3n-E4B-it` model on Hugging Face

3. **GPU Requirements**: Scripts are optimized for CUDA GPUs. CPU inference will be significantly slower

4. **First Run**: Model download (~5GB) happens on first execution

5. **Memory Requirements**: Ensure sufficient GPU memory (recommended: 16GB+ VRAM)

## 🎯 Expected Outputs

- ✅ **Success**: All scripts should show green checkmarks and performance metrics
- ❌ **Failure**: Red X marks indicate issues that need resolution
- ⚡ **Performance**: Speed metrics help optimize your setup

## 🔧 Troubleshooting

- **CUDA Issues**: Ensure proper CUDA and PyTorch versions
- **Memory Errors**: Reduce batch size or use CPU inference
- **Token Errors**: Verify HF token has model access permissions
- **Import Errors**: Check all dependencies are installed correctly

## 📊 Performance Expectations

On RTX 4090:
- Model loading: ~10-30 seconds (first time: +download time)
- Text generation: ~15-30 tokens/second
- Image processing: ~2-5 seconds per image

These scripts ensure your environment is properly configured for optimal Gemma 3n performance!

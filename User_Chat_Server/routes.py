# routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils import classify_emergency, get_model_info
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Request/Response models
class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    category: str

class ModelInfoResponse(BaseModel):
    model_loaded: bool
    categories: list
    model_path: str
    device: str

@router.post("/ask_class", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """
    Classify emergency text into predefined categories
    
    Categories: child_lost, crowd_panic, lost_item, medical_help, need_interpreter, small_fire
    """
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Classify
        category = classify_emergency(request.text.strip())
        
        # Log the request
        logger.info(f"Classification: '{request.text}' -> '{category}'")
        
        return ClassificationResponse(category=category)
        
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail="Classification failed")

@router.get("/model_info", response_model=ModelInfoResponse)
async def model_info():
    """Get model information and status"""
    try:
        info = get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")

@router.get("/debug")
async def debug_info():
    """Debug information about model status"""
    from utils import model, tokenizer
    return {
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None,
        "model_type": str(type(model)) if model else "None",
        "tokenizer_type": str(type(tokenizer)) if tokenizer else "None",
        "model_device": str(model.device) if model else "None",
        "categories": get_model_info()["categories"]
    }
async def batch_classify(requests: list[ClassificationRequest]):
    """Classify multiple texts at once"""
    try:
        results = []
        for req in requests:
            if req.text and req.text.strip():
                category = classify_emergency(req.text.strip())
                results.append({
                    "text": req.text,
                    "category": category
                })
            else:
                results.append({
                    "text": req.text,
                    "category": "error",
                    "error": "empty_text"
                })
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Batch classification error: {e}")
        raise HTTPException(status_code=500, detail="Batch classification failed")
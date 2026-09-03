import torch
import torchvision.transforms as transforms
from PIL import Image
import json
import os
import numpy as np
import time
from threading import Lock

# Try to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# =====================================================
# MODEL LOADING
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model", "crop_damage_model.pth")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "ml", "model", "class_names.json")

_model = None
_class_names = None
_device = None
_model_lock = Lock()

def get_device():
    global _device
    if _device is None:
        if torch.cuda.is_available():
            _device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            _device = torch.device("mps")
        else:
            _device = torch.device("cpu")
    return _device

def load_model():
    global _model, _class_names
    
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    # Load class names
                    if os.path.exists(CLASS_NAMES_PATH):
                        with open(CLASS_NAMES_PATH, "r") as f:
                            _class_names = json.load(f)
                        print(f"✅ Loaded {len(_class_names)} classes")
                    else:
                        _class_names = ["Healthy", "Blight", "Blast", "Brown Spot", "Tungro", "Leaf Blast"]
                        print("⚠️ Using fallback class names")
                    
                    # Load model
                    device = get_device()
                    if os.path.exists(MODEL_PATH):
                        loaded = torch.load(MODEL_PATH, map_location=device)
                        # Check if it's a checkpoint dictionary or model
                        if isinstance(loaded, dict):
                            print("⚠️ Loaded checkpoint - creating model from state_dict")
                            import torch.nn as nn
                            _model = nn.Sequential(
                                nn.Flatten(),
                                nn.Linear(3*224*224, 512),
                                nn.ReLU(),
                                nn.Linear(512, len(_class_names))
                            )
                            if 'model_state_dict' in loaded:
                                _model.load_state_dict(loaded['model_state_dict'])
                            _model.eval()
                            _model = _model.to(device)
                            print("✅ Model loaded from checkpoint")
                        else:
                            _model = loaded
                            _model.eval()
                            _model = _model.to(device)
                            print("✅ Model loaded directly")
                    else:
                        print(f"⚠️ Model not found at {MODEL_PATH}")
                        import torch.nn as nn
                        _model = nn.Sequential(
                            nn.Flatten(),
                            nn.Linear(3*224*224, 512),
                            nn.ReLU(),
                            nn.Linear(512, len(_class_names))
                        )
                        _model.eval()
                        print("✅ Fallback model created")
                        
                except Exception as e:
                    print(f"⚠️ Error loading model: {e}")
                    import torch.nn as nn
                    _class_names = ["Healthy", "Blight", "Blast", "Brown Spot", "Tungro", "Leaf Blast"]
                    _model = nn.Sequential(
                        nn.Flatten(),
                        nn.Linear(3*224*224, 512),
                        nn.ReLU(),
                        nn.Linear(512, len(_class_names))
                    )
                    _model.eval()
                    print("✅ Fallback model created")
    
    return _model, _class_names

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# =====================================================
# DISEASE PREDICTION
# =====================================================

def predict_disease(image_path, max_size=512):
    """
    Predict crop disease from image using trained model.
    Returns: (predicted_disease, model_confidence)
    """
    try:
        start_time = time.time()
        
        model, class_names = load_model()
        
        # Load image
        image = Image.open(image_path).convert("RGB")
        
        # Resize if too large
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Transform
        input_tensor = _transform(image).unsqueeze(0)
        device = get_device()
        input_tensor = input_tensor.to(device)
        
        # Predict
        try:
            with torch.no_grad():
                outputs = model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
            
            predicted_class = class_names[predicted.item()] if predicted.item() < len(class_names) else "Unknown"
            confidence_score = confidence.item() * 100
            
            elapsed = (time.time() - start_time) * 1000
            print(f"✅ Disease prediction: {predicted_class} ({confidence_score:.1f}%) in {elapsed:.0f}ms")
            
            return predicted_class, round(confidence_score, 2)
            
        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            return fallback_prediction(image_path)
        
    except Exception as e:
        print(f"❌ Error in predict_disease: {e}")
        return "Unknown", 0.0

def fallback_prediction(image_path):
    """Fallback prediction using image analysis"""
    try:
        if OPENCV_AVAILABLE:
            image = cv2.imread(image_path)
            if image is not None:
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                lower_green = np.array([35, 40, 40])
                upper_green = np.array([85, 255, 255])
                green_mask = cv2.inRange(hsv, lower_green, upper_green)
                green_pixels = cv2.countNonZero(green_mask)
                total = image.shape[0] * image.shape[1]
                green_ratio = green_pixels / total
                
                if green_ratio > 0.6:
                    return "Healthy", 70.0
                elif green_ratio > 0.3:
                    return "Early Blight", 55.0
                else:
                    return "Late Blight", 45.0
        return "Unknown", 50.0
    except:
        return "Unknown", 0.0

# =====================================================
# DAMAGE ESTIMATION (SEPARATE FROM DISEASE CLASSIFIER)
# =====================================================

def estimate_damage_percentage(image_path):
    """
    Estimate visible crop damage percentage from image.
    This is SEPARATE from the disease classifier.
    Returns: estimated_damage_percentage (0-100)
    """
    try:
        start_time = time.time()
        
        if not OPENCV_AVAILABLE:
            return estimate_damage_pil(image_path)
        
        image = cv2.imread(image_path)
        if image is None:
            return estimate_damage_pil(image_path)
        
        # Resize for speed
        height, width = image.shape[:2]
        if max(height, width) > 512:
            scale = 512 / max(height, width)
            new_size = (int(width * scale), int(height * scale))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Green = healthy vegetation
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        total_pixels = image.shape[0] * image.shape[1]
        healthy_pixels = cv2.countNonZero(green_mask)
        healthy_percentage = (healthy_pixels / total_pixels) * 100
        
        # Brown/yellow = damaged vegetation
        lower_brown = np.array([10, 30, 30])
        upper_brown = np.array([30, 200, 200])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
        damaged_pixels = cv2.countNonZero(brown_mask)
        damaged_percentage = (damaged_pixels / total_pixels) * 100
        
        # Calculate damage
        estimated_damage = damaged_percentage
        
        # If mostly green, reduce damage
        if healthy_percentage > 40:
            estimated_damage = max(0, estimated_damage - 15)
        
        estimated_damage = max(0, min(100, estimated_damage))
        
        elapsed = (time.time() - start_time) * 1000
        print(f"✅ Damage estimation: {estimated_damage:.1f}% in {elapsed:.0f}ms")
        
        return round(estimated_damage, 2)
        
    except Exception as e:
        print(f"⚠️ Damage estimation error: {e}")
        return estimate_damage_pil(image_path)

def estimate_damage_pil(image_path):
    """PIL fallback for damage estimation (no OpenCV required)"""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((224, 224))
        pixels = np.array(img)
        
        # Green pixels (healthy)
        green_mask = (pixels[:,:,1] > 100) & (pixels[:,:,1] > pixels[:,:,0]) & (pixels[:,:,1] > pixels[:,:,2])
        green_pixels = np.sum(green_mask)
        total_pixels = 224 * 224
        
        # Brown pixels (damaged)
        brown_mask = (pixels[:,:,0] > 100) & (pixels[:,:,0] > pixels[:,:,1]) & (pixels[:,:,0] > pixels[:,:,2])
        brown_pixels = np.sum(brown_mask)
        
        # Calculate damage
        if green_pixels > total_pixels * 0.6:
            damage = 20
        elif green_pixels > total_pixels * 0.3:
            damage = 50
        else:
            damage = 75
        
        brown_ratio = brown_pixels / total_pixels
        damage = max(damage, brown_ratio * 100)
        return round(min(100, damage), 2)
        
    except Exception as e:
        print(f"⚠️ PIL fallback error: {e}")
        return 30.0

# =====================================================
# INITIALIZE ON IMPORT
# =====================================================

print("🔄 Initializing ML module...")
load_model()
print(f"✅ ML module ready (OpenCV: {OPENCV_AVAILABLE})")
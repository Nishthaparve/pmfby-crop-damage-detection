import json
import re
import secrets
import shutil
import hashlib
import uuid
from pathlib import Path
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from fastapi import File, Form, UploadFile, FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.hash import pbkdf2_sha256
from jose import jwt, JWTError
import ee
import difflib
from datetime import datetime, timedelta
import os
import numpy as np

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SQLITE DATABASE SETUP - COMPLETELY FIXED
# =========================================================

DB_PATH = BASE_DIR / "backend" / "claims.db"

def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
# =========================================================
# AUTHENTICATION (JWT)
# Defined early because the endpoints below (e.g. /analyze, /claims)
# reference get_current_user in their Depends() default arguments,
# and those defaults are evaluated the moment the endpoint is defined.
# =========================================================
SECRET_KEY = "pmfby-crop-damage-secret-key-change-in-production"
ALGORITHM = "HS256"


def get_current_user(authorization: str = Header(None)):
    # Parse the Bearer JWT and return the authenticated user row.
    credentials_exception = HTTPException(
        status_code=401,
        detail="Authentication required. Please login or register to use this feature."
    )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise credentials_exception
    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
    user = cursor.fetchone()
    connection.close()

    if user is None:
        raise credentials_exception
    return user

def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT NOT NULL,"
        "phone TEXT NOT NULL,"
        "email TEXT NOT NULL UNIQUE,"
        "state TEXT NOT NULL,"
        "district TEXT NOT NULL,"
        "username TEXT NOT NULL UNIQUE,"
        "password_hash TEXT NOT NULL,"
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS password_reset_tokens ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "user_id INTEGER NOT NULL,"
        "token_hash TEXT NOT NULL UNIQUE,"
        "expires_at DATETIME NOT NULL,"
        "used INTEGER DEFAULT 0,"
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS claims ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "claim_id TEXT UNIQUE,"
        "user_id INTEGER DEFAULT NULL,"
        "crop TEXT NOT NULL,"
        "claimed_loss REAL NOT NULL,"
        "estimated_damage REAL,"
        "difference REAL,"
        "farm_area REAL NOT NULL,"
        "location TEXT NOT NULL,"
        "district TEXT NOT NULL,"
        "state TEXT NOT NULL,"
        "predicted_disease TEXT,"
        "model_confidence REAL,"
        "uploaded_file TEXT,"
        "review_status TEXT,"
        "review_reason TEXT,"
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    )

    cursor.execute("PRAGMA table_info(claims)")
    claim_columns = [row["name"] for row in cursor.fetchall()]
    if "user_id" not in claim_columns:
        cursor.execute("ALTER TABLE claims ADD COLUMN user_id INTEGER DEFAULT NULL")

    connection.commit()
    connection.close()
    print("Database initialized (users, password_reset_tokens, claims)")

initialize_database()

# =========================================================
# ML MODEL SETUP
# =========================================================

ML_MODEL_PATH = BASE_DIR / "ml" / "model" / "crop_damage_model.pth"
CLASS_NAMES_PATH = BASE_DIR / "ml" / "model" / "class_names.json"
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ML_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

crop_model = None
class_names = []
model_loaded = False

# =========================================================
# LOAD TRAINED MODEL
# =========================================================

def load_crop_model():
    global crop_model, class_names, model_loaded

    if not ML_MODEL_PATH.exists():
        print(f"❌ ML model not found at: {ML_MODEL_PATH}")
        return

    if not CLASS_NAMES_PATH.exists():
        print(f"❌ Class names file not found at: {CLASS_NAMES_PATH}")
        return

    try:
        with open(CLASS_NAMES_PATH, "r") as file:
            class_names = json.load(file)

        # Load MobileNetV2 with correct architecture
        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = nn.Linear(model.last_channel, len(class_names))

        checkpoint = torch.load(ML_MODEL_PATH, map_location=ML_DEVICE)

        # Handle different checkpoint formats
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        model = model.to(ML_DEVICE)
        model.eval()

        crop_model = model
        model_loaded = True

        print(f"✅ PyTorch crop image model loaded successfully.")
        print(f"   Classes: {len(class_names)}")
        print(f"   Device: {ML_DEVICE}")

    except Exception as error:
        print(f"❌ Failed to load PyTorch model: {error}")

# =========================================================
# IMAGE TRANSFORM
# =========================================================

image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# =========================================================
# PREDICT FUNCTION - REAL AI
# =========================================================

def predict_crop_image(image_path):
    if crop_model is None or not model_loaded:
        raise HTTPException(
            status_code=500,
            detail="Crop image model is not loaded. Please check the trained model files."
        )

    try:
        image = Image.open(image_path).convert("RGB")
        image_tensor = image_transform(image).unsqueeze(0).to(ML_DEVICE)

        with torch.no_grad():
            output = crop_model(image_tensor)
            probabilities = torch.softmax(output, dim=1)
            confidence, predicted_index = torch.max(probabilities, 1)

        predicted_class = class_names[predicted_index.item()]
        confidence_percentage = confidence.item() * 100

        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence_percentage, 2)
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Image prediction failed: {str(error)}"
        )

# =========================================================
# IMAGE DAMAGE ESTIMATION - SEPARATE FROM DISEASE CLASSIFIER
# =========================================================

def estimate_image_damage(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((224, 224))
        pixels = np.array(img)

        # Green pixels (healthy vegetation)
        green_mask = (pixels[:,:,1] > 100) & (pixels[:,:,1] > pixels[:,:,0]) & (pixels[:,:,1] > pixels[:,:,2])
        green_pixels = np.sum(green_mask)
        total_pixels = 224 * 224

        # Brown/yellow pixels (damaged)
        brown_mask = (pixels[:,:,0] > 100) & (pixels[:,:,0] > pixels[:,:,1]) & (pixels[:,:,0] > pixels[:,:,2])
        brown_pixels = np.sum(brown_mask)

        # Calculate damage based on color analysis
        if green_pixels > total_pixels * 0.6:
            damage = 20
        elif green_pixels > total_pixels * 0.3:
            damage = 50
        else:
            damage = 75

        # Adjust based on brown pixels
        brown_ratio = brown_pixels / total_pixels
        damage = max(damage, brown_ratio * 100)

        return round(min(100, damage), 2)

    except Exception as e:
        print(f"⚠️ Damage estimation error: {e}")
        return 0.0

# =========================================================
# GENERATE CLAIM ID
# =========================================================

def generate_claim_id():
    return f"CLAIM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

# =========================================================
# CALCULATE REVIEW STATUS
# =========================================================

def calculate_review_status(claimed_loss, estimated_damage):
    if estimated_damage is None or estimated_damage == 0:
        return {
            "status": "HIGH REVIEW",
            "level": "high",
            "difference": 0,
            "reason": "AI image analysis could not estimate damage. Manual verification required."
        }

    difference = abs(claimed_loss - estimated_damage)

    if difference <= 15:
        return {
            "status": "NORMAL REVIEW",
            "level": "normal",
            "difference": round(difference, 2),
            "reason": "Your claim is reasonably consistent with the AI-estimated visible crop damage."
        }
    elif difference <= 30:
        return {
            "status": "MEDIUM REVIEW",
            "level": "medium",
            "difference": round(difference, 2),
            "reason": "Moderate difference detected. Additional verification is required."
        }
    else:
        return {
            "status": "HIGH REVIEW",
            "level": "high",
            "difference": round(difference, 2),
            "reason": "Significant inconsistency detected. High-priority manual review required."
        }

# Load the trained ML model when backend starts
load_crop_model()

# =========================================================
# GOOGLE EARTH ENGINE CONFIGURATION
# =========================================================

EE_PROJECT = "pmfby-crop-damage-detection"
EE_INITIALIZED = False
EE_INITIALIZATION_ERROR = None

try:
    ee.Initialize(project=EE_PROJECT)
    EE_INITIALIZED = True
    print("✅ Google Earth Engine initialized successfully.")
    print(f"   Project: {EE_PROJECT}")

except Exception as error:
    EE_INITIALIZATION_ERROR = str(error)
    print("\n❌ GOOGLE EARTH ENGINE INITIALIZATION FAILED")
    print(error)

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="PMFBY Crop Damage Detection API",
    description="AI & Satellite-based crop damage detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for async tasks
executor = ThreadPoolExecutor(max_workers=2)

# =========================================================
# REQUEST MODEL
# =========================================================

class AnalysisRequest(BaseModel):
    district: str
    state: str
    before_start: str
    before_end: str
    after_start: str
    after_end: str

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "message": "PMFBY Crop Damage Detection Backend",
        "earth_engine_initialized": EE_INITIALIZED,
        "model_loaded": model_loaded,
        "project": EE_PROJECT
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "earth_engine": "connected" if EE_INITIALIZED else "not initialized",
        "model_loaded": model_loaded,
        "project": EE_PROJECT
    }

# =========================================================
# DATE VALIDATION
# =========================================================

def validate_dates(request):
    try:
        before_start = datetime.strptime(request.before_start, "%Y-%m-%d")
        before_end = datetime.strptime(request.before_end, "%Y-%m-%d")
        after_start = datetime.strptime(request.after_start, "%Y-%m-%d")
        after_end = datetime.strptime(request.after_end, "%Y-%m-%d")

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Dates must be in YYYY-MM-DD format."
        )

    if before_start >= before_end:
        raise HTTPException(
            status_code=400,
            detail="Before-event start date must be earlier than before-event end date."
        )

    if after_start >= after_end:
        raise HTTPException(
            status_code=400,
            detail="After-event start date must be earlier than after-event end date."
        )

# =========================================================
# DISTRICT GEOMETRY FUNCTION
# =========================================================

def get_district_geometry(state, district):
    districts = ee.FeatureCollection("FAO/GAUL/2015/level2")

    state = state.strip()
    district = district.strip()
    district_lower = district.lower()

    # Aliases for common cities
    aliases = {
        "mumbai": ["Mumbai City", "Mumbai Suburban", "Greater Bombay"],
        "bombay": ["Mumbai City", "Mumbai Suburban", "Greater Bombay"],
        "bangalore": ["Bangalore Urban", "Bengaluru Urban"],
        "bengaluru": ["Bangalore Urban", "Bengaluru Urban"],
        "calcutta": ["Kolkata"],
        "kolkata": ["Kolkata"],
        "new delhi": ["New Delhi"],
        "delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"]
    }

    # Get all districts inside selected state
    state_districts = districts.filter(ee.Filter.eq("ADM1_NAME", state))
    available_districts = state_districts.aggregate_array("ADM2_NAME").getInfo()

    if not available_districts:
        raise HTTPException(
            status_code=404,
            detail=f"State '{state}' was not found in the boundary dataset."
        )

    # Special alias handling
    if district_lower in aliases:
        possible_names = aliases[district_lower]
        matching_features = ee.FeatureCollection([])
        found_names = []

        for possible_name in possible_names:
            matching = state_districts.filter(ee.Filter.eq("ADM2_NAME", possible_name))
            count = matching.size().getInfo()

            if count > 0:
                matching_features = matching_features.merge(matching)
                found_names.append(possible_name)

        if found_names:
            return matching_features.geometry(), district

    # Exact case-insensitive match
    for available in available_districts:
        if available.lower() == district_lower:
            feature = state_districts.filter(ee.Filter.eq("ADM2_NAME", available))
            return feature.geometry(), available

    # Partial match
    partial_matches = []
    for available in available_districts:
        available_lower = available.lower()
        if district_lower in available_lower or available_lower in district_lower:
            partial_matches.append(available)

    if partial_matches:
        matched_name = partial_matches[0]
        feature = state_districts.filter(ee.Filter.eq("ADM2_NAME", matched_name))
        return feature.geometry(), matched_name

    # Fuzzy match
    lower_to_original = {name.lower(): name for name in available_districts}
    closest = difflib.get_close_matches(district_lower, list(lower_to_original.keys()), n=1, cutoff=0.65)

    if closest:
        matched_name = lower_to_original[closest[0]]
        feature = state_districts.filter(ee.Filter.eq("ADM2_NAME", matched_name))
        return feature.geometry(), matched_name

    raise HTTPException(
        status_code=404,
        detail=f"District '{district}' was not found in state '{state}'."
    )

# =========================================================
# SENTINEL-2 CLOUD MASK
# =========================================================

def mask_sentinel_clouds(image):
    scl = image.select("SCL")
    mask = (
        scl.neq(0).And(scl.neq(1)).And(scl.neq(3))
        .And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
        .And(scl.neq(11))
    )
    return image.updateMask(mask)

# =========================================================
# GET SENTINEL-2 IMAGE
# =========================================================

def get_sentinel_image(start_date, end_date, geometry):
    raw_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
    )

    raw_count = raw_collection.size().getInfo()

    if raw_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No Sentinel-2 images found between {start_date} and {end_date}."
        )

    preferred_collection = (
        raw_collection
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
        .map(mask_sentinel_clouds)
    )

    preferred_count = preferred_collection.size().getInfo()

    if preferred_count > 0:
        image = preferred_collection.median().clip(geometry)
        valid_pixels = (
            image.select("B8")
            .reduceRegion(
                reducer=ee.Reducer.count(),
                geometry=geometry,
                scale=500,
                maxPixels=1e13,
                bestEffort=True
            )
            .get("B8")
            .getInfo()
        )

        if valid_pixels and valid_pixels > 0:
            return image, preferred_count

    # Fallback
    fallback_image = raw_collection.median().clip(geometry)
    return fallback_image, raw_count

# =========================================================
# CALCULATE NDVI
# =========================================================

def calculate_ndvi(image):
    return image.normalizedDifference(["B8", "B4"]).rename("NDVI")

# =========================================================
# SAFE REDUCE REGION HELPER
# =========================================================

def get_region_value(image, band_name, geometry):
    result = image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=100,
        maxPixels=1e13,
        bestEffort=True
    )
    value = result.get(band_name).getInfo()
    return value if value is not None else 0

# =========================================================
# SATELLITE ANALYSIS ENDPOINT
# =========================================================

@app.post("/analyze")
def analyze_crop_damage(request: AnalysisRequest, user=Depends(get_current_user)):
    if not EE_INITIALIZED:
        raise HTTPException(
            status_code=500,
            detail=f"Google Earth Engine is not initialized. {EE_INITIALIZATION_ERROR}"
        )

    validate_dates(request)

    print(f"\n🛰️ Analyzing {request.district}, {request.state}")
    print(f"   Before: {request.before_start} to {request.before_end}")
    print(f"   After: {request.after_start} to {request.after_end}")

    # Get district geometry
    geometry, matched_district = get_district_geometry(request.state, request.district)

    # Get Sentinel-2 images
    before_image, before_count = get_sentinel_image(
        request.before_start, request.before_end, geometry
    )
    after_image, after_count = get_sentinel_image(
        request.after_start, request.after_end, geometry
    )

    # Calculate NDVI
    before_ndvi = calculate_ndvi(before_image)
    after_ndvi = calculate_ndvi(after_image)
    ndvi_change = after_ndvi.subtract(before_ndvi).rename("NDVI_Change")

    # Vegetation mask (NDVI >= 0.15)
    vegetation_mask = before_ndvi.gte(0.15)

    # Damage mask (NDVI change <= -0.05 and vegetation)
    damage_mask = ndvi_change.lte(-0.05).And(vegetation_mask)

    # Calculate areas
    pixel_area = ee.Image.pixelArea()

    vegetation_area_image = pixel_area.updateMask(vegetation_mask)
    total_area_m2 = get_region_value(vegetation_area_image, "area", geometry)
    total_area_ha = total_area_m2 / 10000

    damage_area_image = pixel_area.updateMask(damage_mask)
    damage_area_m2 = get_region_value(damage_area_image, "area", geometry)
    damage_area_ha = damage_area_m2 / 10000

    damage_percentage = (damage_area_ha / total_area_ha) * 100 if total_area_ha > 0 else 0

    # Mean NDVI values
    before_ndvi_value = (
        before_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=100,
            maxPixels=1e13,
            bestEffort=True
        ).get("NDVI").getInfo() or 0
    )

    after_ndvi_value = (
        after_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=100,
            maxPixels=1e13,
            bestEffort=True
        ).get("NDVI").getInfo() or 0
    )

    ndvi_change_value = (
        ndvi_change.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=100,
            maxPixels=1e13,
            bestEffort=True
        ).get("NDVI_Change").getInfo() or 0
    )

    # Create map
    map_image = ndvi_change.clip(geometry).visualize(
        min=-0.30,
        max=0.30,
        palette=["red", "orange", "yellow", "white", "lightgreen", "green"]
    )
    map_id = ee.Image(map_image).getMapId()
    map_url = map_id["tile_fetcher"].url_format

    # ---- Real district bounds for frontend map viewport (fitBounds) ----
    # Purely additive: reads the bounding box of the SAME geometry object
    # already used above for the NDVI/damage analysis. Does not alter any
    # Earth Engine computation, mask, or the map tile generation itself.
    bounds_geojson = geometry.bounds(1).getInfo()
    bounds_coords = bounds_geojson["coordinates"][0]
    bounds_lons = [pt[0] for pt in bounds_coords]
    bounds_lats = [pt[1] for pt in bounds_coords]
    district_bounds = {
        "south": min(bounds_lats),
        "west": min(bounds_lons),
        "north": max(bounds_lats),
        "east": max(bounds_lons)
    }

    print(f"✅ Analysis complete!")
    print(f"   Total area: {total_area_ha:.2f} ha")
    print(f"   Damage area: {damage_area_ha:.2f} ha")
    print(f"   Damage: {damage_percentage:.2f}%")

    return {
        "status": "success",
        "study_area": {
            "state": request.state,
            "district": matched_district,
            "bounds": district_bounds
        },
        "periods": {
            "before": {"start": request.before_start, "end": request.before_end},
            "after": {"start": request.after_start, "end": request.after_end}
        },
        "satellite_data": {
            "source": "Sentinel-2",
            "platform": "Google Earth Engine",
            "before_images": before_count,
            "after_images": after_count
        },
        "results": {
            "total_area_hectares": round(total_area_ha, 2),
            "potential_damaged_area_hectares": round(damage_area_ha, 2),
            "damage_percentage": round(damage_percentage, 2),
            "before_ndvi": round(before_ndvi_value, 4),
            "after_ndvi": round(after_ndvi_value, 4),
            "ndvi_change": round(ndvi_change_value, 4)
        },
        "maps": {
            "damage_url": map_url
        }
    }

# =========================================================
# SUBMIT CLAIM - REAL AI WITH PROPER MODEL TRAINING
# =========================================================

@app.post("/submit-claim")
async def submit_claim(
    crop: str = Form(...),
    claimed_loss: float = Form(...),
    area: float = Form(...),
    location: str = Form(...),
    district: str = Form(...),
    state: str = Form(...),
    image: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    REAL AI INSURANCE CLAIM - Uses trained MobileNetV2 model

    The model actually processes the image and returns:
    1. Disease prediction (from trained model)
    2. Model confidence (from trained model)
    3. Image damage estimation (separate image analysis)

    Review status is based on comparison between claimed loss and estimated damage.
    """

    # Validation
    if claimed_loss < 0 or claimed_loss > 100:
        raise HTTPException(status_code=400, detail="Claimed loss must be between 0 and 100.")

    if area <= 0:
        raise HTTPException(status_code=400, detail="Farm area must be greater than 0.")

    if image.content_type not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG and WEBP images are allowed.")

    # Save image
    extension = Path(image.filename or "").suffix.lower() or ".jpg"
    unique_filename = f"{uuid.uuid4()}{extension}"
    image_path = UPLOAD_DIR / unique_filename

    try:
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        print(f"📝 Processing claim for {crop}, {district}, {state}")
        print(f"   Claimed loss: {claimed_loss}%")

        # STEP 1: REAL AI DISEASE PREDICTION (TRAINED MODEL)
        print("🧠 Running AI disease prediction...")
        prediction = predict_crop_image(image_path)
        predicted_disease = prediction["predicted_class"]
        model_confidence = prediction["confidence"]
        print(f"   ✅ Disease: {predicted_disease}")
        print(f"   ✅ Confidence: {model_confidence}%")

        # STEP 2: SEPARATE IMAGE DAMAGE ESTIMATION
        print("📊 Estimating image damage...")
        estimated_damage = estimate_image_damage(image_path)
        print(f"   ✅ Estimated damage: {estimated_damage}%")

        # STEP 3: CALCULATE REVIEW STATUS
        review = calculate_review_status(claimed_loss, estimated_damage)
        print(f"   ✅ Review status: {review['status']}")

        # Generate claim ID
        claim_id = generate_claim_id()

        # STEP 4: SAVE TO DATABASE
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO claims (
                claim_id, user_id, crop, claimed_loss, estimated_damage, difference,
                farm_area, location, district, state,
                predicted_disease, model_confidence,
                uploaded_file, review_status, review_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_id,
            user["id"],
            crop,
            claimed_loss,
            estimated_damage,
            review.get("difference"),
            area,
            location,
            district,
            state,
            predicted_disease,
            model_confidence,
            unique_filename,
            review["status"],
            review["reason"]
        ))

        conn.commit()
        claim_db_id = cursor.lastrowid
        conn.close()

        print(f"✅ Claim {claim_id} saved to database")

        # STEP 5: RETURN RESPONSE
        return {
            "status": "success",
            "claim_id": claim_id,
            "claim_db_id": claim_db_id,
            "farmer_claim": {
                "crop": crop,
                "claimed_loss_percentage": round(claimed_loss, 2),
                "farm_area": area,
                "location": location,
                "district": district,
                "state": state
            },
            "image_analysis": {
                "predicted_crop_disease": predicted_disease,
                "model_confidence": model_confidence,
                "estimated_damage_percentage": estimated_damage
            },
            "claim_verification": {
                "review_status": review["status"],
                "level": review["level"],
                "claimed_loss": round(claimed_loss, 2),
                "estimated_damage": round(estimated_damage, 2),
                "difference": review.get("difference", 0),
                "reason": review["reason"]
            }
        }

    except HTTPException:
        raise
    except Exception as error:
        print(f"❌ Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim processing failed: {str(error)}"
        )
    finally:
        await image.close()

# =========================================================
# GET ALL CLAIMS
# =========================================================

def normalize_claim_status(status):
    value = str(status or "").strip().upper()

    if "HIGH" in value:
        return "HIGH REVIEW"
    elif "MEDIUM" in value or "MANUAL" in value:
        return "MEDIUM REVIEW"
    elif "NORMAL" in value:
        return "NORMAL REVIEW"
    else:
        return "PENDING"

@app.get("/claims")
def get_claims(user=Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM claims WHERE user_id = ? ORDER BY id DESC", (user["id"],))
        rows = cursor.fetchall()
        conn.close()

        claims = []
        for row in rows:
            claims.append({
                "id": row["id"],
                "claim_id": row["claim_id"],
                "crop": row["crop"],
                "claimedLoss": row["claimed_loss"],
                "estimatedDamage": row["estimated_damage"] or 0,
                "difference": row["difference"] or 0,
                "farmArea": row["farm_area"],
                "location": row["location"],
                "district": row["district"],
                "state": row["state"],
                "prediction": row["predicted_disease"] or "Unknown",
                "confidence": row["model_confidence"] or 0,
                "status": normalize_claim_status(row["review_status"]),
                "reason": row["review_reason"] or "No reason provided",
                "submittedAt": row["created_at"]
            })

        return claims

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load claim history: {str(error)}"
        )

# =========================================================
# DELETE CLAIM
# =========================================================

@app.delete("/claims/{claim_id}")
def delete_claim(claim_id: int, user=Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT uploaded_file FROM claims WHERE id = ? AND user_id = ?", (claim_id, user["id"]))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Claim not found or you do not own this claim.")

        uploaded_file = row["uploaded_file"]

        cursor.execute("DELETE FROM claims WHERE id = ? AND user_id = ?", (claim_id, user["id"]))
        conn.commit()
        conn.close()

        if uploaded_file:
            uploaded_path = UPLOAD_DIR / uploaded_file
            if uploaded_path.exists():
                uploaded_path.unlink()

        return {"status": "success", "message": "Claim deleted successfully."}

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to delete claim: {str(error)}"
        )

# =========================================================
# CLAIM STATISTICS
# =========================================================

@app.get("/claims/statistics")
def get_claim_statistics(user=Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM claims WHERE user_id = ?", (user["id"],))
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as normal FROM claims WHERE user_id = ? AND review_status = 'NORMAL REVIEW'", (user["id"],))
        normal = cursor.fetchone()["normal"]

        cursor.execute("SELECT COUNT(*) as medium FROM claims WHERE user_id = ? AND review_status = 'MEDIUM REVIEW'", (user["id"],))
        medium = cursor.fetchone()["medium"]

        cursor.execute("SELECT COUNT(*) as high FROM claims WHERE user_id = ? AND review_status = 'HIGH REVIEW'", (user["id"],))
        high = cursor.fetchone()["high"]

        conn.close()

        return {
            "total": total,
            "normal_review": normal,
            "medium_review": medium,
            "high_review": high
        }

    except Exception as error:
        return {"total": 0, "normal_review": 0, "medium_review": 0, "high_review": 0}

# =========================================================
# AUTHENTICATION
# =========================================================

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
RESET_TOKEN_EXPIRE_MINUTES = 30
# Valid Indian states / union territories (mirrors frontend dropdown)
VALID_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu", "Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
}

# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:
    # Hash a plaintext password using PBKDF2-SHA256 (passlib).
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    # Verify a plaintext password against a stored hash.""""
    try:
        return pbkdf2_sha256.verify(password, password_hash)
    except Exception:
        return False
# =========================================================
# JWT TOKENS
# =========================================================

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def serialize_user(user) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "phone": user["phone"],
        "email": user["email"],
        "state": user["state"],
        "district": user["district"],
        "username": user["username"],
        "created_at": user["created_at"]
    }


def generate_reset_token():
    # Generate a secure one-time reset token and its SHA-256 hash.
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash
# =========================================================
# AUTH REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: str
    state: str
    district: str
    username: str
    password: str
    confirm_password: str
class LoginRequest(BaseModel):
    username: str
    password: str
class ForgotPasswordRequest(BaseModel):
    username: str
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
class UpdateProfileRequest(BaseModel):
    name: str
    phone: str
    email: str
    username: str
    state: str
    district: str
# =========================================================
# AUTH ENDPOINTS
# =========================================================

@app.post("/auth/register")
def register_user(request: RegisterRequest):
    name = request.name.strip()
    phone = request.phone.strip()
    email = request.email.strip().lower()
    state = request.state.strip()
    district = request.district.strip()
    username = request.username.strip()
    password = request.password
    confirm_password = request.confirm_password
    if not name or not phone or not email or not state or not district or not username or not password:
        raise HTTPException(status_code=400, detail="All fields are required.")

    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    phone_regex = r"^[6-9]\d{9}$"
    if not re.match(phone_regex, phone):
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit Indian mobile number.")

    if state not in VALID_STATES:
        raise HTTPException(status_code=400, detail="Please select a valid Indian state.")

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    password_hash = hash_password(password)

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, phone, email, state, district, username, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, email, state, district, username, password_hash)
        )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.close()
        raise HTTPException(
            status_code=409,
            detail="Username or email already registered. Please login or use a different username/email."
        )

    user_id = cursor.lastrowid
    connection.close()

    # Auto-login after registration
    token = create_access_token(user_id)
    user = {
        "id": user_id,
        "name": name,
        "phone": phone,
        "email": email,
        "state": state,
        "district": district,
        "username": username,
        "created_at": ""
    }

    return {
        "status": "success",
        "message": "Registration successful.",
        "token": token,
        "user": user
    }

@app.post("/auth/login")
def login_user(request: LoginRequest):
    username = request.username.strip()
    password = request.password
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    connection.close()

    if user is None or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(user["id"])
    return {
        "status": "success",
        "message": "Login successful.",
        "token": token,
        "user": serialize_user(user)
    }

@app.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    username = request.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Please enter your username.")

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username.lower()))
    user = cursor.fetchone()

    if user is None:
        connection.close()
        raise HTTPException(status_code=404, detail="No account found with that username or email.")

    raw_token, token_hash = generate_reset_token()
    expires_at = (datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used) VALUES (?, ?, 0)",
        (user["id"], token_hash, expires_at)
    )
    connection.commit()
    connection.close()

    # Development-friendly flow: return the token so it can be used in the
    # local reset step without an email service. In production, this token
    # would be emailed to the user instead.
    return {
        "status": "success",
        "message": "Password reset token generated. It expires in 30 minutes.",
        "token": raw_token
    }

@app.post("/auth/reset-password")
def reset_password(request: ResetPasswordRequest):
    token = request.token.strip()
    new_password = request.new_password
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and new password are required.")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM password_reset_tokens WHERE token_hash = ? AND used = 0",
        (token_hash,)
    )
    reset_row = cursor.fetchone()

    if reset_row is None:
        connection.close()
        raise HTTPException(status_code=400, detail="Invalid or already used reset token.")

    try:
        expires_at = datetime.strptime(reset_row["expires_at"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        expires_at = datetime.min
    if datetime.utcnow() > expires_at:
        connection.close()
        raise HTTPException(status_code=400, detail="This reset token has expired. Please request a new one.")

    new_hash = hash_password(new_password)

    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, reset_row["user_id"]))
    cursor.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = ?", (reset_row["id"],))
    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Password has been reset successfully. You can now login with your new password."
    }

@app.get("/auth/me")
def auth_me(user=Depends(get_current_user)):
    return {"status": "success", "user": serialize_user(user)}

@app.put("/auth/profile")
def update_profile(request: UpdateProfileRequest, user=Depends(get_current_user)):
    name = request.name.strip()
    phone = request.phone.strip()
    email = request.email.strip().lower()
    username = request.username.strip()
    state = request.state.strip()
    district = request.district.strip()

    if not name or not phone or not email or not username or not state or not district:
        raise HTTPException(status_code=400, detail="All fields are required.")

    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    phone_regex = r"^[6-9]\d{9}$"
    if not re.match(phone_regex, phone):
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit Indian mobile number.")

    if state not in VALID_STATES:
        raise HTTPException(status_code=400, detail="Please select a valid Indian state.")

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Username/email must stay unique, but the user's own current row doesn't count.
    cursor.execute(
        "SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?",
        (username, email, user["id"])
    )
    conflict = cursor.fetchone()
    if conflict:
        connection.close()
        raise HTTPException(
            status_code=409,
            detail="That username or email is already in use by another account."
        )

    try:
        cursor.execute(
            """UPDATE users
               SET name = ?, phone = ?, email = ?, username = ?, state = ?, district = ?
               WHERE id = ?""",
            (name, phone, email, username, state, district, user["id"])
        )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.close()
        raise HTTPException(
            status_code=409,
            detail="That username or email is already in use by another account."
        )

    cursor.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
    updated_user = cursor.fetchone()
    connection.close()

    # Re-issue the token: if the username changed, future /auth/me and
    # protected calls in this session should keep working seamlessly
    # (the token itself only encodes the numeric user id, not username).
    token = create_access_token(updated_user["id"])

    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "token": token,
        "user": serialize_user(updated_user)
    }

@app.post("/auth/logout")
def logout_user():
    # JWT is stateless; the frontend simply discards the token.
    return {"status": "success", "message": "Logged out successfully."}

# =========================================================
# MAIN ENTRY POINT
# =========================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting PMFBY Crop Damage Detection API")
    print(f"   - Model Loaded: {model_loaded}")
    print(f"   - Earth Engine: {EE_INITIALIZED}")
    print(f"   - Database: {DB_PATH}")
    print(f"   - Uploads: {UPLOAD_DIR}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
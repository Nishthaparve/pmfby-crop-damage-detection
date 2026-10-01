# PMFBY Crop Damage Detection

## Dataset

This project uses the **PlantVillage Dataset** for crop disease classification.

- **Total Images:** 54,305
- **Number of Classes:** 38 crop/disease classes
- **Training Images:** 43,444
- **Validation Images:** 5,439
- **Test Images:** 5,422
- **Split:** 80% Training, 10% Validation, 10% Testing
- **Model:** MobileNetV2 using transfer learning
- **Image Size:** 128 × 128

The dataset is used to train the MobileNetV2 model for identifying crop diseases from uploaded leaf images.

The full PlantVillage dataset is **not included in this GitHub repository** because of its large size. The trained model is already included in the repository, so the dataset is mainly required when retraining or evaluating the model.

Expected local dataset structure:

datasets/
└── plant_village/
    └── PlantVillage/
        ├── Apple___Apple_scab/
        ├── Apple___Black_rot/
        ├── Apple___Cedar_apple_rust/
        ├── ...
        └── Tomato___healthy/

## How to Run the Project

### Step 1: Clone the Repository

git clone https://github.com/Nishthaparve/pmfby-crop-damage-detection.git
cd pmfby-crop-damage-detection

### Step 2: Run the Backend

Open a terminal in the project folder and run:

.\backend\venv\Scripts\Activate.ps1
$env:CLAIM_RISK_MODE="demo"
$env:PYTHONIOENCODING="utf-8"
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload

Backend will run at:

http://127.0.0.1:8000

### Step 3: Run the Frontend

Open a **new terminal**:

cd pmfby-crop-damage-detection\frontend
npm install
npm run dev

Frontend will run at:

http://localhost:5173

### Step 4: Open the Website

Open this in your browser:

http://localhost:5173

## Important

- Keep both the backend and frontend terminals running.
- Create your own `.env` file with the required API keys and configuration.
- The `datasets/` folder is not included in GitHub.
- The trained MobileNetV2 model is included in `ml/model/`.
- The PlantVillage dataset is required only for model training/retraining and evaluation.

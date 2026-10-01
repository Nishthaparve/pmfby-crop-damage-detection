PMFBY Crop Damage Detection & Claim Verification System

An AI/ML-based web application for supporting crop-insurance claim assessment using crop-image classification, computer vision, satellite vegetation analysis, weather verification, and claim-risk triage.

Project status: Academic prototype / demonstration system. AI outputs are decision-support evidence; final insurance claim decisions are made by an authorized human reviewer.

Key Features

Farmer registration, login, profile, password reset, and claim history

Crop/disease image classification using MobileNetV2 (PyTorch)

Visual damage estimation using OpenCV HSV image processing

Sentinel-2 + NDVI vegetation-change analysis through Google Earth Engine

ERA5-Land rainfall and temperature verification through Google Earth Engine

Claim-risk review triage using a calibrated gradient-boosted ML classifier

AI/ML Performance page with accuracy, precision, recall, F1-score, graphs, and confusion matrix

Multilingual UI with English + 11 Indian languages

PMFBY Assistant using a local intent layer and Google Gemini for open-ended questions

Interactive maps using Leaflet

SQLite-backed claim storage

Technology Stack

Frontend

React

Vite

CSS

Leaflet

Backend

Python

FastAPI

SQLite

AI / ML

PyTorch

torchvision

MobileNetV2

scikit-learn

joblib

Computer Vision

OpenCV

Geospatial / Weather

Google Earth Engine

Sentinel-2

NDVI

ECMWF ERA5-Land

Generative AI

Google Gemini API

Project Structure

PMFBY/
├── backend/
│   ├── main.py
│   ├── assistant.py
│   ├── weather_analysis.py
│   ├── claims.db                 # local database, not committed
│   ├── uploads/                  # uploaded claim images, not committed
│   └── venv/                     # Python virtual environment, not committed
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── Chatbot.jsx
│   │   ├── AimlPerformance.jsx
│   │   ├── WeatherVerificationCard.jsx
│   │   └── i18n/
│   └── package.json
│
├── ml/
│   ├── predict.py
│   ├── evaluate_model.py
│   ├── train_improved_mobilenet.py
│   ├── claim_risk.py
│   ├── data/
│   │   └── claim_risk_demo_dataset.csv
│   └── model/
│       ├── crop_damage_model.pth
│       ├── class_names.json
│       ├── dataset_split_info.json
│       └── mobilenet_v2_evaluation_report.json
│
├── datasets/                     # local dataset storage; keep large image datasets outside GitHub
├── .env                          # local secrets; never commit
├── .gitignore
├── README.md
└── requirements.txt

Important Dataset Note

The PlantVillage image dataset is large and should not be uploaded to this GitHub repository.

The repository contains the trained MobileNetV2 checkpoint and the training/evaluation code. Each teammate should download the dataset separately and place it in the local datasets/ directory using the folder structure expected by the training script.

The current MobileNetV2 evaluation is based on a dataset of 54,305 images across 38 classes, with a train/validation/test split of 43,444 / 5,439 / 5,422 images.

The smaller claim-risk demonstration dataset can remain in the repository because it is a CSV and is used for the demo ML pipeline.

Prerequisites

Install:

Python 3.13+ (use the project's existing environment where possible)

Node.js and npm

Git

A Google Earth Engine-enabled Google account/project for satellite and weather analysis

A Gemini API key for the chatbot's generative-AI layer

First-Time Setup

1. Clone the repository

git clone https://github.com/Nishthaparve/pmfby-crop-damage-detection.git
cd pmfby-crop-damage-detection

2. Backend virtual environment

From the project root:

cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

Install Python dependencies:

pip install -r ..\requirements.txt

If PowerShell blocks activation, run PowerShell as appropriate for your local environment or use the environment's Python directly:

.\venv\Scripts\python.exe -m pip install -r ..\requirements.txt

3. Environment variables

Create a .env file in the project root.

At minimum, configure the keys required by the current environment, for example:

GEMINI_API_KEY=your_gemini_api_key
CLAIM_RISK_MODE=demo

Do not commit .env to GitHub.

4. Google Earth Engine

Authenticate / initialize Google Earth Engine for the Google Cloud project used by the application.

Example initialization test:

cd backend
.\venv\Scripts\python.exe -c "import ee; ee.Initialize(project='pmfby-crop-damage-detection'); print('Earth Engine initialized')"

Use your own configured Earth Engine project if it differs from the example above.

Dataset Setup

Download the PlantVillage dataset separately and place it under the local datasets/ folder.

Do not add the full image dataset to GitHub because of its size and repository-management overhead.

Before training, confirm that the local dataset structure matches what ml/train_improved_mobilenet.py expects.

Run the Backend

From the project root:

cd backend
.\venv\Scripts\Activate.ps1
$env:CLAIM_RISK_MODE="demo"
.\venv\Scripts\python.exe -m uvicorn main:app --reload

The backend will normally be available at:

http://127.0.0.1:8000

FastAPI documentation is available at:

http://127.0.0.1:8000/docs

Run the Frontend

Open a second terminal in the project root:

cd frontend
npm install
npm run dev

Open the Vite URL shown in the terminal, normally similar to:

http://localhost:5173

Run Both During Development

Terminal 1 — Backend

cd C:\Users\user\OneDrive\Documents\Desktop\PMFBY\backend
.\venv\Scripts\Activate.ps1
$env:CLAIM_RISK_MODE="demo"
.\venv\Scripts\python.exe -m uvicorn main:app --reload

Terminal 2 — Frontend

cd C:\Users\user\OneDrive\Documents\Desktop\PMFBY\frontend
npm run dev

MobileNetV2 Evaluation

The repository contains the trained checkpoint and the evaluation script.

Run evaluation from the project root using the project's backend virtual environment:

.\backend\venv\Scripts\python.exe ml\evaluate_model.py

The evaluation should report the metrics generated from the available evaluation/test data, including:

Accuracy

Precision

Recall

F1-score

Confusion Matrix

The current reported MobileNetV2 test results are:

Metric

Value

Test Accuracy

93.43%

Macro Precision

90.77%

Macro Recall

93.83%

Macro F1-Score

91.67%

Weighted F1-Score

93.60%

Training Accuracy

94.22%

Validation Accuracy

93.22%

MobileNetV2 Training / Fine-Tuning

The training script is:

ml/train_improved_mobilenet.py

Run it only after the local PlantVillage dataset has been set up correctly:

.\backend\venv\Scripts\python.exe ml\train_improved_mobilenet.py

The training pipeline uses transfer learning with ImageNet-pretrained MobileNetV2, data augmentation, dropout, CrossEntropyLoss with label smoothing, AdamW, weight decay, and cosine learning-rate scheduling.

Do not retrain the model just before a demonstration unless you have enough time to evaluate and verify the new checkpoint.

Claim-Risk Demo Model

The project also contains a demonstration claim-risk model trained from the available claim-risk demo dataset.

The current demo evaluation results are:

Metric

Value

Accuracy

92.11%

Precision

94.44%

Recall

89.47%

F1-Score

91.89%

ROC-AUC

97.92%

The claim-risk model is a decision-support / review-triage component. It must not be represented as a production PMFBY payout or automatic approval/rejection model.

Main Processing Flow

Farmer Claim
    |
    +--> Crop Image --> MobileNetV2 --> Disease/Crop Prediction + Confidence
    |
    +--> Crop Image --> OpenCV HSV --> Visible Damage Heuristic
    |
    +--> Location/Date --> Sentinel-2 --> NDVI Before/After --> Potential Vegetation Loss
    |
    +--> Location/Date/Event --> ERA5-Land --> Rainfall/Temperature Anomalies
    |
    +----------------------------------------------+
                                                   |
                                                   v
                                      Claim Risk ML Model
                                                   |
                                      NORMAL / MEDIUM / HIGH
                                                   |
                                                   v
                                             Human Review

Important Implementation Notes

MobileNetV2

MobileNetV2 is the main deep-learning image classifier and predicts one of 38 classes.

Visual Heuristic

OpenCV HSV is a visible-damage estimate. It is not a trained damage-severity regression model.

Sentinel-2 / NDVI

The satellite branch is a remote-sensing analysis module. It compares vegetation conditions before and after the selected event window and uses the implemented NDVI thresholds to identify potential vegetation loss.

Weather Verification

ERA5-Land is used as contextual meteorological evidence. Event rainfall and temperature are compared with the same calendar period from preceding years to compute anomalies and a weather-consistency score.

Claim Risk

The claim-risk classifier uses multiple claim/evidence features. The score is interpreted into review-priority categories. The final insurance decision remains with a human reviewer.

AI/ML Performance Page

The AI/ML Performance page is intended to show model evaluation results rather than process a farmer claim.

The page contains the essential classification metrics and visualizations for the MobileNetV2 model and the claim-risk model.

Troubleshooting

Backend import / package errors

Activate the backend environment and install requirements again:

cd backend
.\venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements.txt

Claim-risk model shows MODEL_NOT_READY

For the current demonstration setup, set:

$env:CLAIM_RISK_MODE="demo"

before starting the backend.

Weather data unavailable

ERA5-Land may not contain the newest dates immediately. Do not replace missing values with fake data. Test with dates that are available in the archive when demonstrating the weather branch.

GitHub / Dataset

Do not commit:

.env
backend/claims.db
backend/uploads/
backend/venv/
full PlantVillage image dataset

The .gitignore file is intended to keep these local/generated resources out of the repository.

Team Collaboration

After cloning the repository, each teammate should:

Install backend dependencies.

Install frontend dependencies.

Obtain the dataset separately if working on model training.

Create their own local .env file.

Pull the latest main branch before making changes.

Create a separate branch for larger changes.

Test the application locally before committing.

Example:

git pull origin main
git checkout -b feature/my-change

After testing:

git add -A
git commit -m "Describe the change"
git push -u origin feature/my-change

Current Model Summary

MobileNetV2

Task: 38-class crop/disease image classification

Framework: PyTorch

Transfer learning: ImageNet

Test Accuracy: 93.43%

Macro F1: 91.67%

Claim Risk Model

Task: Claim inconsistency / review triage

Framework: scikit-learn

Model family: Gradient-boosted decision-tree classifier

Accuracy: 92.11%

F1: 91.89%

ROC-AUC: 97.92%

Supporting Analysis

OpenCV HSV visible-damage heuristic

Sentinel-2 NDVI analysis

ERA5-Land weather verification

Google Gemini assistant

Disclaimer

This project is an academic prototype for demonstrating AI/ML-assisted crop damage assessment and claim verification. Its outputs are intended to support review and analysis. They should not be interpreted as an automated insurance approval, rejection, fraud finding, or payout calculation.

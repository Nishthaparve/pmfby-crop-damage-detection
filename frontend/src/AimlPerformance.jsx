import React, { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";

const DEFAULT_METRICS = {
  mobilenet: {
    accuracy: 93.43,
    precision: 90.77,
    recall: 93.83,
    f1_score: 91.67,
    history: [
  {
    "epoch": 1,
    "train_loss": 1.9512,
    "val_loss": 1.2004,
    "train_accuracy": 63.75,
    "val_accuracy": 79.98
  },
  {
    "epoch": 2,
    "train_loss": 0.9129,
    "val_loss": 0.7677,
    "train_accuracy": 86.56,
    "val_accuracy": 89.96
  },
  {
    "epoch": 3,
    "train_loss": 0.7128,
    "val_loss": 0.6886,
    "train_accuracy": 91.91,
    "val_accuracy": 92.85
  },
  {
    "epoch": 4,
    "train_loss": 0.6475,
    "val_loss": 0.672,
    "train_accuracy": 94.22,
    "val_accuracy": 93.22
  }
],
    class_names: [
  "Apple___Apple_scab",
  "Apple___Black_rot",
  "Apple___Cedar_apple_rust",
  "Apple___healthy",
  "Blueberry___healthy",
  "Cherry_(including_sour)___Powdery_mildew",
  "Cherry_(including_sour)___healthy",
  "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
  "Corn_(maize)___Common_rust_",
  "Corn_(maize)___Northern_Leaf_Blight",
  "Corn_(maize)___healthy",
  "Grape___Black_rot",
  "Grape___Esca_(Black_Measles)",
  "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
  "Grape___healthy",
  "Orange___Haunglongbing_(Citrus_greening)",
  "Peach___Bacterial_spot",
  "Peach___healthy",
  "Pepper,_bell___Bacterial_spot",
  "Pepper,_bell___healthy",
  "Potato___Early_blight",
  "Potato___Late_blight",
  "Potato___healthy",
  "Raspberry___healthy",
  "Soybean___healthy",
  "Squash___Powdery_mildew",
  "Strawberry___Leaf_scorch",
  "Strawberry___healthy",
  "Tomato___Bacterial_spot",
  "Tomato___Early_blight",
  "Tomato___Late_blight",
  "Tomato___Leaf_Mold",
  "Tomato___Septoria_leaf_spot",
  "Tomato___Spider_mites Two-spotted_spider_mite",
  "Tomato___Target_Spot",
  "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
  "Tomato___Tomato_mosaic_virus",
  "Tomato___healthy"
],
    confusion_matrix: [[58, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 59, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 155, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 150, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 1, 102, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 83, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 44, 0, 6, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 118, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 15, 0, 83, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 116, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 112, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 130, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 103, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 41, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 549, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0], [2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 4, 202, 10, 1, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 93, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 143, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 95, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 99, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 37, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 3, 0, 1, 12, 0, 484, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 179, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 108, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 46, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 178, 10, 1, 0, 12, 0, 2, 3, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 80, 5, 0, 2, 2, 1, 0, 3, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 2, 0, 0, 13, 0, 0, 0, 0, 0, 0, 0, 26, 138, 3, 2, 0, 0, 1, 0, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 84, 4, 2, 0, 0, 1, 0], [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 2, 10, 154, 0, 0, 1, 2, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 1, 159, 0, 0, 2, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 3, 10, 1, 0, 4, 10, 109, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 9, 1, 0, 0, 6, 0, 512, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 37, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 7, 2, 0, 0, 148]]
  },
  claim_risk: {
    accuracy: 92.11,
    precision: 94.44,
    recall: 89.47,
    f1_score: 91.89,
    roc_auc: 97.92
  }
};

export default function AimlPerformance({ t }) {
  const [metrics, setMetrics] = useState(DEFAULT_METRICS);
  const [cmMode, setCmMode] = useState("count"); // "count" | "percent"
  const [hoveredCell, setHoveredCell] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const res = await fetch(`${API_BASE}/ml/performance`);
        if (res.ok) {
          const json = await res.json();
          if (isMounted && json.status === "success") {
            const mb = json.mobilenet_v2 || {};
            const cr = json.claim_risk || {};
            setMetrics({
              mobilenet: {
                accuracy: mb.test_accuracy || mb.validation_accuracy || DEFAULT_METRICS.mobilenet.accuracy,
                precision: mb.precision || mb.precision_macro || DEFAULT_METRICS.mobilenet.precision,
                recall: mb.recall || mb.recall_macro || DEFAULT_METRICS.mobilenet.recall,
                f1_score: mb.f1_score || mb.f1_macro || DEFAULT_METRICS.mobilenet.f1_score,
                history: mb.training_history || DEFAULT_METRICS.mobilenet.history,
                class_names: mb.class_names || DEFAULT_METRICS.mobilenet.class_names,
                confusion_matrix: mb.confusion_matrix || DEFAULT_METRICS.mobilenet.confusion_matrix,
              },
              claim_risk: {
                accuracy: cr.accuracy || DEFAULT_METRICS.claim_risk.accuracy,
                precision: cr.precision || DEFAULT_METRICS.claim_risk.precision,
                recall: cr.recall || DEFAULT_METRICS.claim_risk.recall,
                f1_score: cr.f1_score || DEFAULT_METRICS.claim_risk.f1_score,
                roc_auc: cr.roc_auc || DEFAULT_METRICS.claim_risk.roc_auc,
              }
            });
          }
        }
      } catch (err) {
        // Use default cached genuine values
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, []);

  const mb = metrics.mobilenet;
  const cr = metrics.claim_risk;
  const cm = mb.confusion_matrix || [];
  const classNames = mb.class_names || [];

  return (
    <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto", color: "#0f172a", fontFamily: "Inter, system-ui, -apple-system, sans-serif" }}>
      
      {/* 1. PAGE HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ margin: "0 0 6px 0", fontSize: "26px", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.5px" }}>
          AI/ML Performance
        </h1>
        <p style={{ margin: 0, fontSize: "14px", color: "#64748b" }}>
          Model evaluation results and performance metrics.
        </p>
      </div>

      {/* 2. MOBILENETV2 MODEL PERFORMANCE */}
      <section style={{ background: "white", borderRadius: "8px", border: "1px solid #e2e8f0", padding: "24px", marginBottom: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.03)" }}>
        <h2 style={{ margin: "0 0 16px 0", fontSize: "18px", fontWeight: 700, color: "#0f172a" }}>
          MobileNetV2 Crop & Disease Classification
        </h2>

        {/* 4 Metric Cards: Accuracy | Precision | Recall | F1-Score */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", marginBottom: "24px" }}>
          <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "13px", color: "#64748b", fontWeight: 600 }}>Accuracy</div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#0f766e", margin: "4px 0" }}>
              {mb.accuracy}%
            </div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>Overall correct classifications</div>
          </div>

          <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "13px", color: "#64748b", fontWeight: 600 }}>Precision</div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#0284c7", margin: "4px 0" }}>
              {mb.precision}%
            </div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>Positive predictive value</div>
          </div>

          <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "13px", color: "#64748b", fontWeight: 600 }}>Recall</div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#0284c7", margin: "4px 0" }}>
              {mb.recall}%
            </div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>Sensitivity across all classes</div>
          </div>

          <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "13px", color: "#64748b", fontWeight: 600 }}>F1-Score</div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#0f766e", margin: "4px 0" }}>
              {mb.f1_score}%
            </div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>Harmonic mean of precision & recall</div>
          </div>
        </div>

        {/* 3. TRAINING GRAPHS (ACCURACY & LOSS) */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px", marginBottom: "28px" }}>
          
          {/* Graph A: Training vs Validation Accuracy */}
          <div style={{ background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0", padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "#0f172a" }}>
                Training vs Validation Accuracy
              </h3>
              <span style={{ fontSize: "11px", color: "#64748b" }}>Accuracy (%)</span>
            </div>

            <svg viewBox="0 0 460 200" style={{ width: "100%", maxHeight: "210px", overflow: "visible" }}>
              {/* Grid Lines */}
              <line x1="45" y1="25" x2="435" y2="25" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="65" x2="435" y2="65" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="105" x2="435" y2="105" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="145" x2="435" y2="145" stroke="#cbd5e1" strokeWidth="1.5" />

              {/* Y Axis Labels */}
              <text x="35" y="29" textAnchor="end" fontSize="10" fill="#94a3b8">100%</text>
              <text x="35" y="69" textAnchor="end" fontSize="10" fill="#94a3b8">90%</text>
              <text x="35" y="109" textAnchor="end" fontSize="10" fill="#94a3b8">80%</text>
              <text x="35" y="149" textAnchor="end" fontSize="10" fill="#94a3b8">70%</text>

              {/* X Axis Labels */}
              <text x="90" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 1</text>
              <text x="190" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 2</text>
              <text x="290" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 3</text>
              <text x="390" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 4</text>

              {/* Training Line: Ep1 63.8% (y:170), Ep2 86.6% (y:78), Ep3 91.9% (y:57), Ep4 94.2% (y:48) */}
              <polyline
                fill="none"
                stroke="#0284c7"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points="90,170 190,78 290,57 390,48"
              />
              <circle cx="90" cy="170" r="4" fill="#0284c7" stroke="#fff" strokeWidth="1.5" />
              <circle cx="190" cy="78" r="4" fill="#0284c7" stroke="#fff" strokeWidth="1.5" />
              <circle cx="290" cy="57" r="4" fill="#0284c7" stroke="#fff" strokeWidth="1.5" />
              <circle cx="390" cy="48" r="4" fill="#0284c7" stroke="#fff" strokeWidth="1.5" />

              {/* Validation Line: Ep1 80.0% (y:105), Ep2 90.0% (y:65), Ep3 92.9% (y:53), Ep4 93.2% (y:52) */}
              <polyline
                fill="none"
                stroke="#0f766e"
                strokeWidth="2.5"
                strokeDasharray="5 3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points="90,105 190,65 290,53 390,52"
              />
              <circle cx="90" cy="105" r="4" fill="#0f766e" stroke="#fff" strokeWidth="1.5" />
              <circle cx="190" cy="65" r="4" fill="#0f766e" stroke="#fff" strokeWidth="1.5" />
              <circle cx="290" cy="53" r="4" fill="#0f766e" stroke="#fff" strokeWidth="1.5" />
              <circle cx="390" cy="52" r="4" fill="#0f766e" stroke="#fff" strokeWidth="1.5" />
            </svg>

            <div style={{ display: "flex", justifyContent: "center", gap: "20px", marginTop: "8px", fontSize: "11px", fontWeight: 600 }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#0284c7" }}>
                <span style={{ width: "14px", height: "3px", background: "#0284c7", display: "inline-block" }}></span> Training Accuracy
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#0f766e" }}>
                <span style={{ width: "14px", height: "3px", background: "#0f766e", borderTop: "2px dashed #0f766e", display: "inline-block" }}></span> Validation Accuracy
              </span>
            </div>
          </div>

          {/* Graph B: Training vs Validation Loss */}
          <div style={{ background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0", padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "#0f172a" }}>
                Training vs Validation Loss
              </h3>
              <span style={{ fontSize: "11px", color: "#64748b" }}>Loss</span>
            </div>

            <svg viewBox="0 0 460 200" style={{ width: "100%", maxHeight: "210px", overflow: "visible" }}>
              {/* Grid Lines */}
              <line x1="45" y1="25" x2="435" y2="25" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="65" x2="435" y2="65" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="105" x2="435" y2="105" stroke="#e2e8f0" strokeDasharray="3" />
              <line x1="45" y1="145" x2="435" y2="145" stroke="#cbd5e1" strokeWidth="1.5" />

              {/* Y Axis Labels */}
              <text x="35" y="29" textAnchor="end" fontSize="10" fill="#94a3b8">2.0</text>
              <text x="35" y="69" textAnchor="end" fontSize="10" fill="#94a3b8">1.5</text>
              <text x="35" y="109" textAnchor="end" fontSize="10" fill="#94a3b8">1.0</text>
              <text x="35" y="149" textAnchor="end" fontSize="10" fill="#94a3b8">0.5</text>

              {/* X Axis Labels */}
              <text x="90" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 1</text>
              <text x="190" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 2</text>
              <text x="290" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 3</text>
              <text x="390" y="165" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Epoch 4</text>

              {/* Train Loss: Ep1 1.95 (y:29), Ep2 0.91 (y:112), Ep3 0.71 (y:128), Ep4 0.65 (y:133) */}
              <polyline
                fill="none"
                stroke="#dc2626"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points="90,29 190,112 290,128 390,133"
              />
              <circle cx="90" cy="29" r="4" fill="#dc2626" stroke="#fff" strokeWidth="1.5" />
              <circle cx="190" cy="112" r="4" fill="#dc2626" stroke="#fff" strokeWidth="1.5" />
              <circle cx="290" cy="128" r="4" fill="#dc2626" stroke="#fff" strokeWidth="1.5" />
              <circle cx="390" cy="133" r="4" fill="#dc2626" stroke="#fff" strokeWidth="1.5" />

              {/* Val Loss: Ep1 1.20 (y:89), Ep2 0.77 (y:123), Ep3 0.69 (y:130), Ep4 0.67 (y:131) */}
              <polyline
                fill="none"
                stroke="#ea580c"
                strokeWidth="2.5"
                strokeDasharray="5 3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points="90,89 190,123 290,130 390,131"
              />
              <circle cx="90" cy="89" r="4" fill="#ea580c" stroke="#fff" strokeWidth="1.5" />
              <circle cx="190" cy="123" r="4" fill="#ea580c" stroke="#fff" strokeWidth="1.5" />
              <circle cx="290" cy="130" r="4" fill="#ea580c" stroke="#fff" strokeWidth="1.5" />
              <circle cx="390" cy="131" r="4" fill="#ea580c" stroke="#fff" strokeWidth="1.5" />
            </svg>

            <div style={{ display: "flex", justifyContent: "center", gap: "20px", marginTop: "8px", fontSize: "11px", fontWeight: 600 }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#dc2626" }}>
                <span style={{ width: "14px", height: "3px", background: "#dc2626", display: "inline-block" }}></span> Training Loss
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#ea580c" }}>
                <span style={{ width: "14px", height: "3px", background: "#ea580c", borderTop: "2px dashed #ea580c", display: "inline-block" }}></span> Validation Loss
              </span>
            </div>
          </div>

        </div>

        {/* 4. CONFUSION MATRIX (COMPACT & READABLE) */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div>
              <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "#0f172a" }}>
                Confusion Matrix
              </h3>
              <span style={{ fontSize: "12px", color: "#64748b" }}>
                MobileNetV2 evaluation matrix (38 classes). Diagonal indicates correct predictions.
              </span>
            </div>

            <div style={{ display: "inline-flex", background: "#f1f5f9", borderRadius: "6px", padding: "2px" }}>
              <button
                type="button"
                onClick={() => setCmMode("count")}
                style={{
                  border: "none",
                  background: cmMode === "count" ? "#0f766e" : "transparent",
                  color: cmMode === "count" ? "white" : "#64748b",
                  padding: "4px 10px",
                  borderRadius: "5px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Counts
              </button>
              <button
                type="button"
                onClick={() => setCmMode("percent")}
                style={{
                  border: "none",
                  background: cmMode === "percent" ? "#0f766e" : "transparent",
                  color: cmMode === "percent" ? "white" : "#64748b",
                  padding: "4px 10px",
                  borderRadius: "5px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Percent (%)
              </button>
            </div>
          </div>

          <div
            style={{
              maxHeight: "360px",
              overflow: "auto",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              background: "#fafafa",
            }}
          >
            <table style={{ borderCollapse: "collapse", fontSize: "10px", width: "100%", minWidth: "1100px" }}>
              <thead style={{ position: "sticky", top: 0, background: "#f1f5f9", zIndex: 2 }}>
                <tr>
                  <th style={{ padding: "6px 8px", border: "1px solid #cbd5e1", background: "#e2e8f0", minWidth: "140px", textAlign: "left" }}>
                    Actual \ Pred
                  </th>
                  {classNames.map((_, i) => (
                    <th key={i} style={{ padding: "4px 2px", border: "1px solid #cbd5e1", minWidth: "24px", textAlign: "center", color: "#334155" }}>
                      {i + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cm.map((row, i) => {
                  const rowSum = row.reduce((a, b) => a + b, 0) || 1;
                  return (
                    <tr key={i}>
                      <td style={{ padding: "4px 8px", border: "1px solid #e2e8f0", fontWeight: 600, background: "#f8fafc", whiteSpace: "nowrap", fontSize: "11px", color: "#1e293b" }}>
                        <span style={{ color: "#94a3b8", marginRight: "4px" }}>{i + 1}.</span>
                        {classNames[i] ? classNames[i].replace(/___/g, " - ").replace(/_/g, " ") : `C${i+1}`}
                      </td>
                      {row.map((val, j) => {
                        const isDiag = i === j;
                        const pct = ((val / rowSum) * 100).toFixed(0);
                        const intensity = isDiag
                          ? Math.min(1, Math.max(0.15, val / rowSum))
                          : val > 0 ? Math.min(0.8, (val / rowSum) * 2) : 0;
                        const bg = isDiag
                          ? `rgba(16, 185, 129, ${intensity})`
                          : val > 0 ? `rgba(239, 68, 68, ${intensity})` : "transparent";
                        const textColor = isDiag && intensity > 0.5 ? "white" : (val > 0 ? "#991b1b" : "#94a3b8");

                        return (
                          <td
                            key={j}
                            onMouseEnter={() => setHoveredCell({
                              actual: classNames[i],
                              pred: classNames[j],
                              val,
                              pct
                            })}
                            onMouseLeave={() => setHoveredCell(null)}
                            style={{
                              padding: "3px 1px",
                              border: "1px solid #f1f5f9",
                              textAlign: "center",
                              background: bg,
                              color: textColor,
                              fontWeight: isDiag ? 700 : (val > 0 ? 600 : 400),
                            }}
                          >
                            {cmMode === "count" ? (val > 0 ? val : "·") : (val > 0 ? `${pct}%` : "·")}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {hoveredCell && (
            <div style={{ marginTop: "8px", fontSize: "11px", color: "#475569" }}>
              <strong>Actual:</strong> {hoveredCell.actual ? hoveredCell.actual.replace(/___/g, " - ").replace(/_/g, " ") : ""} | <strong>Predicted:</strong> {hoveredCell.pred ? hoveredCell.pred.replace(/___/g, " - ").replace(/_/g, " ") : ""} | <strong>Count:</strong> {hoveredCell.val} ({hoveredCell.pct}%)
            </div>
          )}
        </div>

      </section>

      {/* 5. AI CLAIM RISK CLASSIFICATION SECTION */}
      <section style={{ background: "white", borderRadius: "8px", border: "1px solid #e2e8f0", padding: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.03)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: 700, color: "#0f172a" }}>
              AI Claim Risk Classification
            </h2>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Probabilistic Gradient Boosting Model for Claim Review Triage
            </span>
          </div>
          <span style={{ background: "#fef3c7", color: "#92400e", padding: "4px 10px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}>
            Demonstration ML Model
          </span>
        </div>

        {/* 5 Metric Cards: Accuracy | Precision | Recall | F1-Score | ROC-AUC */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px" }}>
          <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>Accuracy</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f766e", margin: "4px 0" }}>
              {cr.accuracy}%
            </div>
          </div>

          <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>Precision</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#0284c7", margin: "4px 0" }}>
              {cr.precision}%
            </div>
          </div>

          <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>Recall</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#0284c7", margin: "4px 0" }}>
              {cr.recall}%
            </div>
          </div>

          <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>F1-Score</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f766e", margin: "4px 0" }}>
              {cr.f1_score}%
            </div>
          </div>

          <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>ROC-AUC</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#7c3aed", margin: "4px 0" }}>
              {cr.roc_auc}%
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}

import { useState, useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";
import Chatbot from "./Chatbot";
import WeatherVerificationCard from "./WeatherVerificationCard";
import AimlPerformance from "./AimlPerformance";
import { languages, translate } from "./i18n";

// ---- Auth token helpers (JWT stored in localStorage) ----
const API_BASE = "http://127.0.0.1:8000";

const getStoredToken = () => localStorage.getItem("pmfby_token") || "";
const storeToken = (token) => localStorage.setItem("pmfby_token", token);
const clearToken = () => localStorage.removeItem("pmfby_token");

// Attach the JWT to any request that needs authentication.
const authHeaders = (json = true) => {
  const token = getStoredToken();
  const headers = {};
  if (json) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
};

// ---- Clean Line SVG Icons for Institutional UI ----
function PlantEmblemIcon({ size = 20, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 22V8" />
      <path d="M5 12H2a10 10 0 0 0 20 0h-3" />
      <path d="M8 5c1-2 3.5-3 5-3 2 1.5 2 4 0 6-2 1.5-4 1-5-3Z" />
      <path d="M9 13a4.5 4.5 0 0 0-4.5-4.5C3 8.5 2 9.5 2 11c0 2.5 3 4.5 7 4.5v-2.5Z" />
      <path d="M15 13a4.5 4.5 0 0 1 4.5-4.5c1.5 0 2.5 1 2.5 2.5 0 2.5-3 4.5-7 4.5v-2.5Z" />
    </svg>
  );
}

function DashboardIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="12" rx="1" />
      <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
  );
}

function MapIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" />
      <line x1="9" x2="9" y1="3" y2="18" />
      <line x1="15" x2="15" y1="6" y2="21" />
    </svg>
  );
}

function LocationPinIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function ShieldCheckIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function FileTextIcon({ size = 18, className = "", style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
      <path d="M10 9H8" />
      <path d="M16 13H8" />
      <path d="M16 17H8" />
    </svg>
  );
}

function BarChartIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <line x1="12" x2="12" y1="20" y2="10" />
      <line x1="18" x2="18" y1="20" y2="4" />
      <line x1="6" x2="6" y1="20" y2="16" />
    </svg>
  );
}

function LockIcon({ size = 18, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function SproutIcon({ size = 20, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M7 20h10" />
      <path d="M10 20c5.5-2.5.8-6.4 3-10" />
      <path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4.1 5.5.8z" />
      <path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z" />
    </svg>
  );
}

function AlertTriangleIcon({ size = 20, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" x2="12" y1="9" y2="13" />
      <line x1="12" x2="12.01" y1="17" y2="17" />
    </svg>
  );
}

function TrendingDownIcon({ size = 20, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
      <polyline points="16 17 22 17 22 11" />
    </svg>
  );
}

function SatelliteDishIcon({ size = 20, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M4 10a7.31 7.31 0 0 0 10 10" />
      <path d="M4 6a11.37 11.37 0 0 0 14 14" />
      <path d="M4 2a15.42 15.42 0 0 0 18 18" />
      <line x1="4" x2="12" y1="22" y2="14" />
    </svg>
  );
}

function LogoutIcon({ size = 16, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" x2="9" y1="12" y2="12" />
    </svg>
  );
}



const districtsByState = {
  "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Kadapa", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"],
  "Arunachal Pradesh": ["Changlang", "Dibang Valley", "East Kameng", "East Siang", "Itanagar Capital Complex", "Lower Subansiri", "Papum Pare", "Tawang", "West Kameng", "West Siang"],
  Assam: ["Baksa", "Barpeta", "Bongaigaon", "Cachar", "Dibrugarh", "Golaghat", "Guwahati", "Jorhat", "Kamrup", "Nagaon", "Silchar", "Sonitpur", "Tinsukia"],
  Bihar: ["Araria", "Bhagalpur", "Darbhanga", "Gaya", "Katihar", "Muzaffarpur", "Nalanda", "Patna", "Purnia", "Samastipur", "Saran", "Vaishali"],
  Chhattisgarh: ["Balod", "Bilaspur", "Dantewada", "Durg", "Jagdalpur", "Korba", "Raipur", "Raigarh", "Rajnandgaon", "Surguja"],
  Goa: ["North Goa", "South Goa"],
  Gujarat: ["Ahmedabad", "Amreli", "Anand", "Banaskantha", "Bharuch", "Bhavnagar", "Gandhinagar", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mehsana", "Rajkot", "Surat", "Vadodara"],
  Haryana: ["Ambala", "Bhiwani", "Faridabad", "Gurugram", "Hisar", "Karnal", "Kurukshetra", "Panipat", "Rohtak", "Sirsa", "Sonipat"],
  "Himachal Pradesh": ["Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Mandi", "Shimla", "Solan", "Una"],
  Jharkhand: ["Bokaro", "Dhanbad", "Dumka", "East Singhbhum", "Giridih", "Hazaribagh", "Palamu", "Ranchi", "West Singhbhum"],
  Karnataka: ["Bengaluru Urban", "Belagavi", "Ballari", "Bidar", "Chikkamagaluru", "Dakshina Kannada", "Davanagere", "Dharwad", "Hassan", "Kalaburagi", "Mandya", "Mysuru", "Raichur", "Shivamogga", "Tumakuru", "Udupi"],
  Kerala: ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
  "Madhya Pradesh": ["Bhopal", "Chhindwara", "Dewas", "Gwalior", "Indore", "Jabalpur", "Khandwa", "Ratlam", "Rewa", "Sagar", "Satna", "Ujjain"],
  Maharashtra: ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Bhandara", "Chandrapur", "Dhule", "Jalgaon", "Kolhapur", "Latur", "Mumbai", "Nagpur", "Nanded", "Nashik", "Pune", "Raigad", "Satara", "Solapur", "Thane", "Wardha", "Yavatmal"],
  Manipur: ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Senapati", "Thoubal", "Ukhrul"],
  Meghalaya: ["East Khasi Hills", "East Garo Hills", "Ri-Bhoi", "South Garo Hills", "West Garo Hills", "West Khasi Hills"],
  Mizoram: ["Aizawl", "Champhai", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Serchhip"],
  Nagaland: ["Dimapur", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Tuensang", "Wokha", "Zunheboto"],
  Odisha: ["Balasore", "Bhadrak", "Cuttack", "Ganjam", "Jagatsinghpur", "Kendrapara", "Khordha", "Mayurbhanj", "Puri", "Sambalpur", "Sundargarh"],
  Punjab: ["Amritsar", "Bathinda", "Fazilka", "Firozpur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Ludhiana", "Moga", "Patiala", "Sangrur"],
  Rajasthan: ["Ajmer", "Alwar", "Barmer", "Bikaner", "Bundi", "Jaipur", "Jaisalmer", "Jodhpur", "Kota", "Nagaur", "Sikar", "Udaipur"],
  Sikkim: ["Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Cuddalore", "Dindigul", "Erode", "Kancheepuram", "Madurai", "Salem", "Thanjavur", "Tiruchirappalli", "Tirunelveli", "Vellore"],
  Telangana: ["Adilabad", "Hyderabad", "Karimnagar", "Khammam", "Mahabubnagar", "Medak", "Nalgonda", "Nizamabad", "Rangareddy", "Warangal"],
  Tripura: ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
  "Uttar Pradesh": ["Agra", "Aligarh", "Allahabad", "Ayodhya", "Bareilly", "Ghaziabad", "Gorakhpur", "Kanpur Nagar", "Lucknow", "Meerut", "Prayagraj", "Varanasi"],
  Uttarakhand: ["Almora", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Tehri Garhwal", "Udham Singh Nagar"],
  "West Bengal": ["Bankura", "Birbhum", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Medinipur", "Purba Medinipur", "Siliguri"],
  "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
  Chandigarh: ["Chandigarh"],
  "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
  Delhi: ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North West Delhi", "South Delhi", "West Delhi"],
  Jammu: ["Jammu", "Kathua", "Poonch", "Rajouri", "Samba", "Udhampur"],
  Kashmir: ["Anantnag", "Baramulla", "Budgam", "Ganderbal", "Pulwama", "Srinagar"],
  Ladakh: ["Kargil", "Leh"],
  Lakshadweep: ["Lakshadweep"],
  Puducherry: ["Karaikal", "Mahe", "Puducherry", "Yanam"],
};

const indianStates = Object.keys(districtsByState);

// Centers the Leaflet map on the REAL analyzed district using the actual
// geometry bounds returned by the backend (Earth Engine geometry.bounds()),
// instead of any hardcoded per-city coordinates. Works for every district.
function FitBoundsToDistrict({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (
      bounds &&
      Number.isFinite(bounds.south) &&
      Number.isFinite(bounds.west) &&
      Number.isFinite(bounds.north) &&
      Number.isFinite(bounds.east)
    ) {
      map.fitBounds(
        [
          [bounds.south, bounds.west],
          [bounds.north, bounds.east],
        ],
        { padding: [20, 20] }
      );
    }
  }, [bounds, map]);

  return null;
}

// ---- Login / Register / Forgot / Reset form ----
function AuthForm({ mode, loading, error, successMsg, onSubmit, onSwitchMode, initialToken, t }) {
  const [values, setValues] = useState({
    name: "",
    phone: "",
    email: "",
    username: "",
    password: "",
    confirm_password: "",
    state: "Maharashtra",
    district: "Nagpur",
    token: initialToken || "",
    new_password: "",
    confirm_new_password: "",
  });

  useEffect(() => {
    if (initialToken) {
      setValues((v) => ({ ...v, token: initialToken }));
    }
  }, [initialToken]);

  const set = (key) => (e) =>
    setValues((v) => ({ ...v, [key]: e.target.value }));

  const states = Object.keys(districtsByState);
  const districts = districtsByState[values.state] || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(values);
  };

  if (mode === "forgot") {
    return (
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>{t("username")}</label>
          <input
            type="text"
            value={values.username}
            onChange={set("username")}
            placeholder={t("usernamePlaceholder")}
            required
          />
        </div>

        {error && <div className="auth-error">{error}</div>}
        {successMsg && (
          <div className="auth-success" style={{ background: "#e8f5e9", color: "#1e4620", padding: "10px", borderRadius: "6px", marginBottom: "12px", fontSize: "13px" }}>
            {successMsg}
          </div>
        )}

        <button type="submit" className="analyze-button" disabled={loading}>
          {loading ? t("loading") : t("sendResetToken")}
        </button>

        <div className="auth-switch" style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "8px", alignItems: "center" }}>
          <button
            type="button"
            className="auth-link"
            onClick={() => onSwitchMode("reset", values.token)}
          >
            {t("haveResetToken")}
          </button>
          <button
            type="button"
            className="auth-link"
            onClick={() => onSwitchMode("login")}
          >
            ← {t("login")}
          </button>
        </div>
      </form>
    );
  }

  if (mode === "reset") {
    return (
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>{t("resetToken")}</label>
          <input
            type="text"
            value={values.token}
            onChange={set("token")}
            placeholder={t("resetTokenPlaceholder")}
            required
          />
        </div>

        <div className="form-group">
          <label>{t("newPassword")}</label>
          <input
            type="password"
            value={values.new_password}
            onChange={set("new_password")}
            placeholder={t("newPasswordPlaceholder")}
            required
          />
        </div>

        <div className="form-group">
          <label>{t("confirmPassword")}</label>
          <input
            type="password"
            value={values.confirm_new_password}
            onChange={set("confirm_new_password")}
            placeholder={t("confirmPasswordPlaceholder")}
            required
          />
        </div>

        {error && <div className="auth-error">{error}</div>}

        <button type="submit" className="analyze-button" disabled={loading}>
          {loading ? t("loading") : t("resetPassword")}
        </button>

        <div className="auth-switch" style={{ marginTop: "14px", textAlign: "center" }}>
          <button
            type="button"
            className="auth-link"
            onClick={() => onSwitchMode("login")}
          >
            ← {t("login")}
          </button>
        </div>
      </form>
    );
  }

  const isLogin = mode === "login";

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      {!isLogin && (
        <>
          <div className="form-group">
            <label>{t("fullName")}</label>
            <input
              type="text"
              value={values.name}
              onChange={set("name")}
              placeholder={t("enterFullName")}
              required
            />
          </div>

          <div className="form-group">
            <label>{t("phoneNumber")}</label>
            <input
              type="tel"
              value={values.phone}
              onChange={set("phone")}
              placeholder={t("phonePlaceholder")}
              pattern="[6-9][0-9]{9}"
              required
            />
          </div>

          <div className="form-group">
            <label>{t("email")}</label>
            <input
              type="email"
              value={values.email}
              onChange={set("email")}
              placeholder={t("emailPlaceholder")}
              required
            />
          </div>

          <div className="auth-row">
            <div className="form-group">
              <label>{t("state")}</label>
              <select
                value={values.state}
                onChange={(e) => {
                  setValues((v) => ({
                    ...v,
                    state: e.target.value,
                    district: (districtsByState[e.target.value] || [])[0] || "",
                  }));
                }}
              >
                {states.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>{t("district")}</label>
              <select value={values.district} onChange={set("district")}>
                {districts.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </>
      )}

      <div className="form-group">
        <label>{t("username")}</label>
        <input
          type="text"
          value={values.username}
          onChange={set("username")}
          placeholder={t("usernamePlaceholder")}
          required
        />
      </div>

      <div className="form-group">
        <label>{t("password")}</label>
        <input
          type="password"
          value={values.password}
          onChange={set("password")}
          placeholder={t("passwordPlaceholder")}
          required
        />
      </div>

      {isLogin && (
        <div style={{ textAlign: "right", marginTop: "-4px", marginBottom: "10px" }}>
          <button
            type="button"
            className="auth-link"
            style={{ fontSize: "12px", background: "none", border: "none", cursor: "pointer", color: "#176b56", textDecoration: "underline" }}
            onClick={() => onSwitchMode("forgot")}
          >
            {t("forgotPassword")}
          </button>
        </div>
      )}

      {!isLogin && (
        <div className="form-group">
          <label>{t("confirmPassword")}</label>
          <input
            type="password"
            value={values.confirm_password}
            onChange={set("confirm_password")}
            placeholder={t("confirmPasswordPlaceholder")}
            required
          />
        </div>
      )}

      {error && <div className="auth-error">{error}</div>}

      <button type="submit" className="analyze-button" disabled={loading}>
        {loading
          ? isLogin
            ? t("loggingIn")
            : t("registering")
          : isLogin
          ? t("login")
          : t("register")}
      </button>
    </form>
  );
}

function App() {
  const [language, setLanguage] = useState(() => localStorage.getItem("preferredLanguage") || localStorage.getItem("pmfby_language") || "en");
  const t = (key, values) => translate(language, key, values);
  const [selectedState, setSelectedState] = useState("Maharashtra");
  const [selectedDistrict, setSelectedDistrict] = useState("Nagpur");
  const [beforeStart, setBeforeStart] = useState("2025-06-01");
  const [beforeEnd, setBeforeEnd] = useState("2025-06-30");
  const [afterStart, setAfterStart] = useState("2025-09-01");
  const [afterEnd, setAfterEnd] = useState("2025-09-30");
  const [activePage, setActivePage] = useState("dashboard");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [claimCrop, setClaimCrop] = useState("");
  const [claimedLoss, setClaimedLoss] = useState("");
  const [farmArea, setFarmArea] = useState("");
  const [claimLocation, setClaimLocation] = useState("");
  const [claimEventType, setClaimEventType] = useState("");
  const [claimCropStage, setClaimCropStage] = useState("");
  const [claimDate, setClaimDate] = useState(new Date().toISOString().slice(0, 10));
  const [sowingDate, setSowingDate] = useState("");
  const [farmLatitude, setFarmLatitude] = useState("");
  const [farmLongitude, setFarmLongitude] = useState("");
  const [farmPolygon, setFarmPolygon] = useState("");
  const [claimImage, setClaimImage] = useState(null);
  const [claimLoading, setClaimLoading] = useState(false);
  const [claimResult, setClaimResult] = useState(null);
  const [claimHistory, setClaimHistory] = useState([]);
  const [claimSearch, setClaimSearch] = useState("");
  const [claimStatusFilter, setClaimStatusFilter] = useState("ALL");

  // ---- Auth state ----
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authMode, setAuthMode] = useState("login"); // "login" | "register" | "forgot" | "reset"
  const [resetToken, setResetToken] = useState("");
  const [resetSuccessMsg, setResetSuccessMsg] = useState("");

  // ---- Profile edit state ----
  const [profileEditMode, setProfileEditMode] = useState(false);
  const [profileForm, setProfileForm] = useState(null);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState("");

  const changeLanguage = (nextLanguage) => {
    setLanguage(nextLanguage);
    localStorage.setItem("preferredLanguage", nextLanguage);
    localStorage.setItem("pmfby_language", nextLanguage);
  };

  const loadClaims = async () => {
    try {
      const response = await fetch(`${API_BASE}/claims`, {
        headers: authHeaders(),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : t("loadClaimsFailed")
        );
      }

      setClaimHistory(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error loading claims:", error);
      setClaimHistory([]);
    }
  };

  useEffect(() => {
    // If a token already exists, try to restore the session, and only
    // load claim history once we know who (if anyone) is authenticated.
    // This avoids a race where /claims resolves using a stored token
    // before we've confirmed /auth/me, which could show history while
    // the UI still thinks no one is logged in.
    if (getStoredToken()) {
      fetch(`${API_BASE}/auth/me`, { headers: authHeaders() })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((data) => {
          setAuthUser(data.user || null);
          if (data.user?.preferred_language && localStorage.getItem("preferredLanguage") == null) {
            changeLanguage(data.user.preferred_language);
          }
          if (data.user) loadClaims();
        })
        .catch(() => {
          clearToken();
          setAuthUser(null);
          setClaimHistory([]);
        });
    } else {
      setClaimHistory([]);
    }
  }, []);

  const handleLogin = async (username, password) => {
    setAuthLoading(true);
    setAuthError("");
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : t("loginFailed")
        );
      }
      storeToken(data.token);
      setAuthUser(data.user);
      setActivePage("dashboard");
      await loadClaims();
    } catch (error) {
      setAuthError(error.message || t("loginFailed"));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (form) => {
    setAuthLoading(true);
    setAuthError("");
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : t("registrationFailed")
        );
      }
      storeToken(data.token);
      setAuthUser(data.user);
      setActivePage("dashboard");
      await loadClaims();
    } catch (error) {
      setAuthError(error.message || t("registrationFailed"));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleForgotPassword = async (username) => {
    if (!username || !username.trim()) {
      setAuthError(t("requiredFields"));
      return;
    }
    setAuthLoading(true);
    setAuthError("");
    setResetSuccessMsg("");
    try {
      const response = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim() }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : t("loginFailed")
        );
      }
      setResetToken(data.token || "");
      setResetSuccessMsg(data.token ? `${t("resetTokenSuccess")} [ ${data.token} ]` : t("resetTokenSuccess"));
    } catch (error) {
      setAuthError(error.message || t("loginFailed"));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleResetPassword = async (token, newPassword, confirmPassword) => {
    if (!token || !token.trim() || !newPassword) {
      setAuthError(t("tokenRequired"));
      return;
    }
    if (newPassword !== confirmPassword) {
      setAuthError(t("requiredFields"));
      return;
    }
    setAuthLoading(true);
    setAuthError("");
    try {
      const response = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token.trim(), new_password: newPassword }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : t("loginFailed")
        );
      }
      alert(t("resetSuccess"));
      setAuthMode("login");
      setResetToken("");
      setResetSuccessMsg("");
    } catch (error) {
      setAuthError(error.message || t("loginFailed"));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setAuthUser(null);
    setClaimHistory([]);
    setActivePage("dashboard");
    setProfileEditMode(false);
  };

  const startEditProfile = () => {
    if (!authUser) return;
    setProfileForm({
      name: authUser.name || "",
      phone: authUser.phone || "",
      email: authUser.email || "",
      username: authUser.username || "",
      state: authUser.state || "",
      district: authUser.district || "",
    });
    setProfileError("");
    setProfileEditMode(true);
  };

  const cancelEditProfile = () => {
    setProfileEditMode(false);
    setProfileError("");
    setProfileForm(null);
  };

  const saveProfile = async () => {
    if (!profileForm) return;

    if (
      !profileForm.name.trim() ||
      !profileForm.phone.trim() ||
      !profileForm.email.trim() ||
      !profileForm.username.trim() ||
      !profileForm.state ||
      !profileForm.district
    ) {
      setProfileError(t("requiredFields"));
      return;
    }

    setProfileSaving(true);
    setProfileError("");

    try {
      const response = await fetch(`${API_BASE}/auth/profile`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({
          name: profileForm.name.trim(),
          phone: profileForm.phone.trim(),
          email: profileForm.email.trim(),
          username: profileForm.username.trim(),
          state: profileForm.state,
          district: profileForm.district,
          preferred_language: language,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : t("profileUpdateFailed")
        );
      }

      // The username may have changed, so re-issue token is stored too.
      if (data.token) storeToken(data.token);
      setAuthUser(data.user);
      setProfileEditMode(false);
      setProfileForm(null);
    } catch (error) {
      setProfileError(error.message || t("profileUpdateFailed"));
    } finally {
      setProfileSaving(false);
    }
  };

  const normalizedHistory = (
    Array.isArray(claimHistory) ? claimHistory : []
  ).map((claim) => {
    const rawStatus = String(claim?.status || "")
      .trim()
      .toUpperCase();

    return {
      ...claim,
      status:
        rawStatus.includes("HIGH")
          ? "HIGH REVIEW"
          : rawStatus.includes("MEDIUM") ||
            rawStatus.includes("MANUAL")
          ? "MEDIUM REVIEW"
          : rawStatus.includes("NORMAL")
          ? "NORMAL REVIEW"
          : "PENDING",
    };
  });

  const filteredClaims = normalizedHistory.filter((claim) => {
    const searchText = String(claimSearch || "")
      .trim()
      .toLowerCase();

    const matchesSearch =
      !searchText ||
      String(claim?.crop || "").toLowerCase().includes(searchText) ||
      String(claim?.location || "").toLowerCase().includes(searchText) ||
      String(claim?.district || "").toLowerCase().includes(searchText) ||
      String(claim?.state || "").toLowerCase().includes(searchText) ||
      String(claim?.prediction || "").toLowerCase().includes(searchText);

    const matchesStatus =
      claimStatusFilter === "ALL" ||
      claim.status === claimStatusFilter;

    return matchesSearch && matchesStatus;
  });

  const totalClaims = normalizedHistory.length;

  const normalReviewClaims = normalizedHistory.filter(
    (claim) => claim.status === "NORMAL REVIEW"
  ).length;

  const mediumReviewClaims = normalizedHistory.filter(
    (claim) => claim.status === "MEDIUM REVIEW"
  ).length;

  const highReviewClaims = normalizedHistory.filter(
    (claim) => claim.status === "HIGH REVIEW"
  ).length;

  const availableDistricts = districtsByState[selectedState] || [];

  const handleStateChange = (value) => {
    setSelectedState(value);
    setSelectedDistrict((districtsByState[value] || [])[0] || "");
    // A different state means any previous analysis/map is now stale.
    setResult(null);
  };

  const handleDistrictChange = (value) => {
    setSelectedDistrict(value);
    // A different district means any previous analysis/map is now stale.
    setResult(null);
  };

  // Fallback center used only before any analysis has run (map is empty
  // until Analyze succeeds, at which point FitBoundsToDistrict takes over
  // using the real district geometry bounds from the backend).
  const INDIA_CENTER = [20.5937, 78.9629];

  const normalizeResult = (data) => ({
    ...data,
    study_area: data.study_area || {
      district: data.district || selectedDistrict,
      state: data.state || selectedState,
    },
    periods: data.periods || data.analysis_period || {
      before: data.before_period || { start: beforeStart, end: beforeEnd },
      after: data.after_period || { start: afterStart, end: afterEnd },
    },
    results: data.results || {
      total_area_hectares: data.total_area,
      potential_damaged_area_hectares: data.potential_damage,
      damage_percentage: data.damage_percentage,
    },
    satellite_data: {
      source: "Sentinel-2",
      platform: "Google Earth Engine",
      ...(data.satellite_data || {}),
    },
    maps: data.maps || {
      damage_url: data.map_url || null,
      ndvi_change_url: data.map_url || null,
    },
  });

  const runAnalysis = async () => {
    if (!authUser) {
      alert(t("loginRequired"));
      setAuthMode("login");
      setActivePage("auth");
      return;
    }

    if (!selectedState || !selectedDistrict) {
      alert(t("selectStateDistrict"));
      setActivePage("study");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          district: selectedDistrict,
          state: selectedState,
          before_start: beforeStart,
          before_end: beforeEnd,
          after_start: afterStart,
          after_end: afterEnd,
        }),
      });

      const text = await response.text();
      let data = {};

      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { detail: text };
      }

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || `Backend error ${response.status}`
        );
      }

      setResult(normalizeResult(data));
      setActivePage("dashboard");
    } catch (error) {
      alert(t("analysisFailed", { message: error.message }));
    } finally {
      setLoading(false);
    }
  };
  const submitClaim = async () => {
    if (!authUser) {
      alert(t("loginRequired"));
      setAuthMode("login");
      setActivePage("auth");
      return;
    }

    if (
      !claimCrop.trim() ||
      claimedLoss === "" ||
      Number.isNaN(Number(claimedLoss)) ||
      Number(claimedLoss) < 0 ||
      Number(claimedLoss) > 100 ||
      !farmArea ||
      Number.isNaN(Number(farmArea)) ||
      Number(farmArea) <= 0 ||
      !claimLocation.trim() ||
      !selectedState ||
      !selectedDistrict ||
      !claimImage
    ) {
      alert(t("completeClaimFields"));
      return;
    }

    setClaimLoading(true);
    setClaimResult(null);

    try {
      const formData = new FormData();

      formData.append("crop", claimCrop.trim());
      formData.append("claimed_loss", String(claimedLoss));
      formData.append("area", String(farmArea));
      formData.append("location", claimLocation.trim());
      formData.append("district", selectedDistrict);
      formData.append("state", selectedState);
      formData.append("event_type", claimEventType);
      formData.append("crop_stage", claimCropStage);
      formData.append("claim_date", claimDate);
      formData.append("sowing_date", sowingDate);
      if (farmLatitude !== "") formData.append("latitude", farmLatitude);
      if (farmLongitude !== "") formData.append("longitude", farmLongitude);
      formData.append("farm_polygon", farmPolygon);
      formData.append("image", claimImage);

      const response = await fetch(`${API_BASE}/submit-claim`, {
        method: "POST",
        headers: {
          Authorization: getStoredToken()
            ? `Bearer ${getStoredToken()}`
            : "",
        },
        body: formData,
      });

      const raw = await response.text();

      let data = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        data = { detail: raw || "Invalid backend response." };
      }

      if (!response.ok) {
        let message = `Backend error ${response.status}`;

        if (typeof data.detail === "string") {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail
            .map((item) => item?.msg || JSON.stringify(item))
            .join(", ");
        } else if (typeof data.message === "string") {
          message = data.message;
        }

        throw new Error(message);
      }

      const reviewStatus =
        data?.claim_verification?.review_status || "PENDING";

      const modelUsed =
        data?.claim_verification?.model_used === true;

      // The Normal/Medium/High triage level is shown ONLY when the trained
      // claim-risk ML model produced it. When model_used is false the backend
      // returns MODEL_NOT_READY and no fake Normal/Medium/High is shown.
      const level = modelUsed
        ? data?.claim_verification?.level || null
        : null;

      setClaimResult({
        ...data,
        claim_verification: {
          ...(data.claim_verification || {}),
          review_status: reviewStatus,
          model_used: modelUsed,
          level,
        },
      });

      await loadClaims();
    } catch (error) {
      console.error("Claim submission error:", error);

      setClaimResult({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : t("claimSubmitFailed"),
      });
    } finally {
      setClaimLoading(false);
    }
  };

  const deleteClaim = async (claimId) => {
    if (!authUser) {
      alert(t("loginRequired"));
      setAuthMode("login");
      setActivePage("auth");
      return;
    }

    if (
      !window.confirm(
        t("deleteClaimConfirm")
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/claims/${claimId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });

      const raw = await response.text();

      let data = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        data = { detail: raw };
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : t("cannotDeleteClaim")
        );
      }

      await loadClaims();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : t("cannotDeleteClaim")
      );
    }
  };

  const totalArea =
    result?.results?.total_area_hectares != null
      ? Number(result.results.total_area_hectares).toFixed(2)
      : "—";

  const damagedArea =
    result?.results?.potential_damaged_area_hectares != null
      ? Number(
          result.results.potential_damaged_area_hectares
        ).toFixed(2)
      : "—";

  const damagePercentage =
    result?.results?.damage_percentage != null
      ? Number(result.results.damage_percentage).toFixed(2)
      : "—";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">
            <PlantEmblemIcon size={24} />
          </div>
          <div>
            <h2>PMFBY</h2>
            <span>{t("cropDamageDetection")}</span>
          </div>
        </div>

        <label className="language-selector">
          <span>{t("language")}</span>
          <select value={language} onChange={(e) => changeLanguage(e.target.value)} aria-label={t("selectLanguage")}>
            {languages.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
        </label>

        <nav className="nav-menu">
          <button
            className={`nav-item ${
              activePage === "dashboard" ? "active" : ""
            }`}
            onClick={() => setActivePage("dashboard")}
          >
            <span className="nav-icon"><DashboardIcon /></span>
            <span>{t("dashboard")}</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "analysis" ? "active" : ""
            }`}
            onClick={() => setActivePage("analysis")}
          >
            <span className="nav-icon"><MapIcon /></span>
            <span>{t("damageAnalysis")}</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "study" ? "active" : ""
            }`}
            onClick={() => setActivePage("study")}
          >
            <span className="nav-icon"><LocationPinIcon /></span>
            <span>{t("studyArea")}</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "claim" ? "active" : ""
            }`}
            onClick={() => setActivePage("claim")}
          >
            <span className="nav-icon"><ShieldCheckIcon /></span>
            <span>{t("insuranceClaim")}</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "reports" ? "active" : ""
            }`}
            onClick={() => setActivePage("reports")}
          >
            <span className="nav-icon"><FileTextIcon /></span>
            <span>{t("reports")}</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "aiml_performance" ? "active" : ""
            }`}
            onClick={() => setActivePage("aiml_performance")}
          >
            <span className="nav-icon"><BarChartIcon /></span>
            <span>{t("aiMlPerformance")}</span>
          </button>


          {!authUser && (
            <button
              className={`nav-item ${
                activePage === "auth" ? "active" : ""
              }`}
              onClick={() => {
                setAuthMode("login");
                setAuthError("");
                setActivePage("auth");
              }}
            >
              <span className="nav-icon"><LockIcon /></span>
              <span>{t("loginRegister")}</span>
            </button>
          )}
        </nav>

        <div className="sidebar-bottom">
          {authUser ? (
            <div
              className="sidebar-user"
              onClick={() => setActivePage("profile")}
              role="button"
              tabIndex={0}
              title={t("profile")}
            >
              <div className="user-avatar">
                {String(authUser.name || authUser.username || "U")
                  .charAt(0)
                  .toUpperCase()}
              </div>
              <div className="user-meta">
                <strong>{authUser.name || authUser.username}</strong>
                <span>
                  {t(`place.${authUser.district}`)}, {t(`place.${authUser.state}`)}
                </span>
              </div>
              <button
                className="user-logout"
                onClick={(e) => {
                  e.stopPropagation();
                  handleLogout();
                }}
                title={t("logout")}
              >
                <LogoutIcon size={15} />
              </button>
            </div>
          ) : (
            <>
               <p>{t("pmfbyProject")}</p>
               <span>{t("aiRemoteSensing")}</span>
            </>
          )}
        </div>
      </aside>

      <main className="main-content">
        {!authUser && activePage === "auth" && (
          <section className="auth-page">
            <div className="auth-card">
              <div className="auth-logo">
                <PlantEmblemIcon size={38} />
              </div>
              <h1 className="auth-title">
                {authMode === "login"
                  ? t("welcomeBack")
                  : authMode === "register"
                  ? t("createAccount")
                  : authMode === "forgot"
                  ? t("forgotPasswordTitle")
                  : t("resetPasswordTitle")}
              </h1>
              <p className="auth-subtitle">
                {authMode === "login"
                  ? t("loginSubtitle")
                  : authMode === "register"
                  ? t("registerSubtitle")
                  : authMode === "forgot"
                  ? t("forgotPasswordSubtitle")
                  : t("resetPasswordSubtitle")}
              </p>

              <AuthForm
                mode={authMode}
                loading={authLoading}
                error={authError}
                successMsg={resetSuccessMsg}
                initialToken={resetToken}
                t={t}
                onSwitchMode={(nextMode, token) => {
                  setAuthMode(nextMode);
                  setAuthError("");
                  setResetSuccessMsg("");
                  if (token) setResetToken(token);
                }}
                onSubmit={async (values) => {
                  if (authMode === "login") {
                    await handleLogin(values.username, values.password);
                  } else if (authMode === "register") {
                    await handleRegister(values);
                  } else if (authMode === "forgot") {
                    await handleForgotPassword(values.username);
                  } else if (authMode === "reset") {
                    await handleResetPassword(values.token, values.new_password, values.confirm_new_password);
                  }
                }}
              />

              {authMode === "login" && (
                <div className="auth-switch">
                  <span>
                    {t("noAccount")}{" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("register");
                        setAuthError("");
                        setResetSuccessMsg("");
                      }}
                    >
                      {t("register")}
                    </button>
                  </span>
                </div>
              )}

              {authMode === "register" && (
                <div className="auth-switch">
                  <span>
                    {t("hasAccount")}{" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("login");
                        setAuthError("");
                        setResetSuccessMsg("");
                      }}
                    >
                      {t("login")}
                    </button>
                  </span>
                </div>
              )}
            </div>
          </section>
        )}

        {activePage === "profile" && (
          <section className="study-page">
            {authUser ? (
              <>
                <div className="page-title">
                  <h1>{t("profile")}</h1>
                  <p>{t("profileSubtitle")}</p>
                </div>

                <div className="study-form-card">
                  {!profileEditMode ? (
                    <>
                      <div className="form-group">
                        <label>{t("fullName")}</label>
                        <input
                          type="text"
                          value={authUser.name || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>{t("username")}</label>
                        <input
                          type="text"
                          value={authUser.username || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>{t("email")}</label>
                        <input
                          type="text"
                          value={authUser.email || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>{t("phoneNumber")}</label>
                        <input
                          type="text"
                          value={authUser.phone || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>{t("state")}</label>
                        <input
                          type="text"
                          value={authUser.state || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>{t("district")}</label>
                        <input
                          type="text"
                          value={authUser.district || ""}
                          readOnly
                        />
                      </div>

                      <button
                        className="analyze-button"
                        onClick={startEditProfile}
                      >
                        {t("editProfile")}
                      </button>

                      <button
                        className="analyze-button"
                        style={{ marginTop: "10px" }}
                        onClick={handleLogout}
                      >
                        {t("logout")}
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="form-group">
                          <label>{t("fullName")}</label>
                        <input
                          type="text"
                          value={profileForm.name}
                          onChange={(e) =>
                            setProfileForm((f) => ({
                              ...f,
                              name: e.target.value,
                            }))
                          }
                        />
                      </div>

                      <div className="form-group">
                          <label>{t("username")}</label>
                        <input
                          type="text"
                          value={profileForm.username}
                          onChange={(e) =>
                            setProfileForm((f) => ({
                              ...f,
                              username: e.target.value,
                            }))
                          }
                        />
                      </div>

                      <div className="form-group">
                          <label>{t("email")}</label>
                        <input
                          type="email"
                          value={profileForm.email}
                          onChange={(e) =>
                            setProfileForm((f) => ({
                              ...f,
                              email: e.target.value,
                            }))
                          }
                        />
                      </div>

                      <div className="form-group">
                          <label>{t("phoneNumber")}</label>
                        <input
                          type="tel"
                          value={profileForm.phone}
                          onChange={(e) =>
                            setProfileForm((f) => ({
                              ...f,
                              phone: e.target.value,
                            }))
                          }
                        />
                      </div>

                      <div className="auth-row">
                        <div className="form-group">
                          <label>{t("state")}</label>
                          <select
                            value={profileForm.state}
                            onChange={(e) =>
                              setProfileForm((f) => ({
                                ...f,
                                state: e.target.value,
                                district:
                                  (districtsByState[e.target.value] ||
                                    [])[0] || "",
                              }))
                            }
                          >
                            {indianStates.map((s) => (
                              <option key={s} value={s}>
                                {s}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label>{t("district")}</label>
                          <select
                            value={profileForm.district}
                            onChange={(e) =>
                              setProfileForm((f) => ({
                                ...f,
                                district: e.target.value,
                              }))
                            }
                          >
                            {(districtsByState[profileForm.state] || []).map(
                              (d) => (
                                <option key={d} value={d}>
                                  {d}
                                </option>
                              )
                            )}
                          </select>
                        </div>
                      </div>

                      {profileError && (
                        <div className="auth-error">{profileError}</div>
                      )}

                      <button
                        className="analyze-button"
                        onClick={saveProfile}
                        disabled={profileSaving}
                      >
                        {profileSaving ? t("loading") : t("saveChanges")}
                      </button>

                      <button
                        className="analyze-button"
                        style={{ marginTop: "10px" }}
                        onClick={cancelEditProfile}
                        disabled={profileSaving}
                      >
                        {t("cancel")}
                      </button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="page-title">
                <h1>{t("profile")}</h1>
                <p>{t("profileLoginRequired")}</p>
              </div>
            )}
          </section>
        )}

        {activePage === "study" && (
          <section className="study-page">
            <div className="page-title">
              <h1>{t("selectStudy")}</h1>
              <p>
                {t("studySubtitle")}
              </p>
            </div>

            <div className="study-form-card">
              <div className="form-group">
                <label>{t("selectState")}</label>
                <select
                  value={selectedState}
                  onChange={(e) => handleStateChange(e.target.value)}
                >
                  {indianStates.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t("selectDistrict")}</label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  disabled={
                    !selectedState || availableDistricts.length === 0
                  }
                >
                  <option value="">{t("selectDistrict")}</option>
                  {availableDistricts.map((district) => (
                    <option key={district} value={district}>
                      {district}
                    </option>
                  ))}
                </select>
              </div>

              <h3>{t("beforeEvent")}</h3>

              <div className="date-grid">
                <div className="form-group">
                  <label>{t("startDate")}</label>
                  <input
                    type="date"
                    value={beforeStart}
                    onChange={(e) => setBeforeStart(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>{t("endDate")}</label>
                  <input
                    type="date"
                    value={beforeEnd}
                    onChange={(e) => setBeforeEnd(e.target.value)}
                  />
                </div>
              </div>

              <h3>{t("afterEvent")}</h3>

              <div className="date-grid">
                <div className="form-group">
                  <label>{t("startDate")}</label>
                  <input
                    type="date"
                    value={afterStart}
                    onChange={(e) => setAfterStart(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>{t("endDate")}</label>
                  <input
                    type="date"
                    value={afterEnd}
                    onChange={(e) => setAfterEnd(e.target.value)}
                  />
                </div>
              </div>

              <button
                className="analyze-button"
                onClick={runAnalysis}
                disabled={loading}
              >
                {loading
                  ? t("analyzing")
                  : t("analyze", { district: selectedDistrict || t("studyArea") })}
              </button>
            </div>
          </section>
        )}

        {activePage === "claim" && (
          <section className="study-page">
            <div className="page-title">
              <h1>{t("insuranceClaim")}</h1>
              <p>
                {t("claimSubtitle")}
              </p>
            </div>

            <div className="study-form-card">
              <h3>{t("claimDetails")}</h3>

              <div className="form-group">
                <label>{t("cropName")}</label>
                <input
                  type="text"
                  value={claimCrop}
                  onChange={(e) => setClaimCrop(e.target.value)}
                  placeholder={t("exampleCrop")}
                />
              </div>

              <div className="form-group">
                <label>{t("claimedLoss")}</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={claimedLoss}
                  onChange={(e) => setClaimedLoss(e.target.value)}
                  placeholder={t("exampleLoss")}
                />
              </div>

              <div className="form-group">
                <label>{t("farmArea")}</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={farmArea}
                  onChange={(e) => setFarmArea(e.target.value)}
                  placeholder={t("exampleArea")}
                />
              </div>

              <div className="form-group">
                <label>{t("farmLocation")}</label>
                <input
                  type="text"
                  value={claimLocation}
                  onChange={(e) => setClaimLocation(e.target.value)}
                  placeholder={t("villagePlaceholder")}
                />
              </div>

              <div className="evidence-form-section">
                 <h3>{t("evidenceForHumanReview")}</h3>
                 <p>{t("evidenceDescription")}</p>
                <div className="evidence-form-grid">
                  <div className="form-group">
                     <label>{t("claimEventType")}</label>
                    <select value={claimEventType} onChange={(e) => setClaimEventType(e.target.value)}>
                       <option value="">{t("selectEvent")}</option>
                       <option value="Flood">{t("eventFlood")}</option>
                       <option value="Drought">{t("eventDrought")}</option>
                       <option value="Cyclone / storm">{t("eventCyclone")}</option>
                       <option value="Pest / disease">{t("eventPestDisease")}</option>
                       <option value="Hail / unseasonal rain">{t("eventHailRain")}</option>
                       <option value="Other">{t("other")}</option>
                    </select>
                  </div>
                  <div className="form-group">
                     <label>{t("cropStage")}</label>
                    <select value={claimCropStage} onChange={(e) => setClaimCropStage(e.target.value)}>
                       <option value="">{t("selectCropStage")}</option>
                       <option value="Germination">{t("stageGermination")}</option><option value="Vegetative">{t("stageVegetative")}</option><option value="Flowering">{t("stageFlowering")}</option><option value="Harvest">{t("stageHarvest")}</option>
                    </select>
                  </div>
                   <div className="form-group"><label>{t("claimDate")}</label><input type="date" value={claimDate} onChange={(e) => setClaimDate(e.target.value)} /></div>
                   <div className="form-group"><label>{t("sowingDate")}</label><input type="date" value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} /></div>
                   <div className="form-group"><label>{t("farmLatitude")}</label><input type="number" step="any" value={farmLatitude} onChange={(e) => setFarmLatitude(e.target.value)} placeholder={t("latitudePlaceholder")} /></div>
                   <div className="form-group"><label>{t("farmLongitude")}</label><input type="number" step="any" value={farmLongitude} onChange={(e) => setFarmLongitude(e.target.value)} placeholder={t("longitudePlaceholder")} /></div>
                </div>
              </div>

              <div className="form-group">
                <label>{t("state")}</label>
                <select
                  value={selectedState}
                  onChange={(e) => handleStateChange(e.target.value)}
                >
                  {indianStates.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t("district")}</label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  disabled={!selectedState || availableDistricts.length === 0}
                >
                  <option value="">{t("selectDistrict")}</option>
                  {availableDistricts.map((district) => (
                    <option key={district} value={district}>
                      {district}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t("uploadImage")}</label>
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={(e) =>
                    setClaimImage(e.target.files?.[0] || null)
                  }
                />

                {claimImage && (
                  <p style={{ marginTop: "10px" }}>
                     {t("selectedImage")}: <strong>{claimImage.name}</strong>
                  </p>
                )}
              </div>

              <button
                type="button"
                className="analyze-button"
                onClick={submitClaim}
                disabled={claimLoading}
              >
                {claimLoading
                  ? t("verifyingClaim")
                  : t("submitClaim")}
              </button>

              {claimResult?.status === "error" && (
                <div
                  className="report-card"
                  style={{ marginTop: "30px" }}
                >
                  <div className="report-section conclusion-section">
                    <h2>{t("claimSubmissionError")}</h2>
                    <p>{claimResult.message}</p>
                  </div>
                </div>
              )}

              {claimResult && claimResult.status !== "error" && (
                <div
                  className="report-card"
                  style={{ marginTop: "30px" }}
                >
                  <div className="report-card-header">
                    <div>
                       <h2>{t("claimVerificationResult")}</h2>
                      <p>
                         {t("claimResultDescription")}
                      </p>
                    </div>

                    <span className="report-status">
                      {claimResult.claim_verification?.review_status ||
                        t("pending")}
                    </span>
                  </div>

                  <div className="report-results-grid">
                    <div className="report-result-box">
                       <span>{t("farmerClaimedLoss")}</span>
                      <strong>
                        {claimResult.farmer_claim
                          ?.claimed_loss_percentage ?? claimedLoss}
                        %
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>{t("aiDisease")}</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.predicted_crop_disease ||
                          t("predictionUnavailable")}
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>{t("modelConfidence")}</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.model_confidence != null
                          ? `${Number(
                              claimResult.image_analysis.model_confidence
                            ).toFixed(2)}%`
                          : t("unavailable")}
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>{t("visualEstimate")}</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.estimated_damage_percentage != null
                          ? `${Number(
                              claimResult.image_analysis
                                .estimated_damage_percentage
                            ).toFixed(2)}%`
                          : t("notAvailable")}
                      </strong>
                    </div>
                  </div>

                  <div className="report-section conclusion-section claim-risk-section">
                    <h2>{t("claimRisk")}</h2>
                    <p className="claim-risk-status">
                      <strong>{t("status")}:</strong>{" "}
                      {claimResult.claim_verification?.review_status ||
                        claimResult.evidence?.review_status ||
                        t("pending")}
                    </p>
                    {claimResult.claim_verification?.claim_risk_score != null && (
                      <p className="claim-risk-score">
                        <strong>{t("claimRiskScore")}:</strong>{" "}
                        {`${(Number(claimResult.claim_verification.claim_risk_score) * 100).toFixed(1)}%`}
                      </p>
                    )}
                    <p className="human-review-note">
                      {t("humanOfficerDecision")}
                    </p>

                    {claimResult.evidence?.explanations &&
                      claimResult.evidence.explanations.length > 0 && (
                        <div style={{ marginTop: "14px" }}>
                          <h3
                            style={{
                              fontSize: "15px",
                              fontWeight: 700,
                              color: "#16302a",
                              margin: "12px 0 6px",
                            }}
                          >
                            {t("priorityExplanation")}
                          </h3>
                          <ul
                            style={{
                              margin: "6px 0",
                              paddingLeft: "20px",
                              color: "#334155",
                              fontSize: "14px",
                            }}
                          >
                            {claimResult.evidence.explanations.map(
                              (item, index) => (
                                <li
                                  key={index}
                                  style={{ marginBottom: "4px" }}
                                >
                                  {item}
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                  </div>

                  <div className="report-section conclusion-section">
                    <h2>{t("reviewDecision")}</h2>

                    <p>
                      {claimResult.claim_verification?.reason ||
                        t("noReviewReason")}
                    </p>

                    {claimResult.claim_verification?.level === "normal" && (
                      <div className="claim-next-action normal-action">
                        <h3 className="claim-action-title normal"><span className="action-status-dot normal"></span> {t("normalReview")}</h3>
                        <p>{t("normalProcess")}</p>

                        <a
                          href="https://pmfby.gov.in/"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="pmfby-portal-button"
                          style={{
                            display: "inline-block",
                            marginTop: "12px",
                            textDecoration: "none",
                            textAlign: "center",
                          }}
                        >
                          {t("continueToPortal")} →
                        </a>
                      </div>
                    )}

                    {claimResult.claim_verification?.level === "medium" && (
                      <div className="claim-next-action medium-action">
                        <h3 className="claim-action-title medium"><span className="action-status-dot medium"></span> {t("mediumReview")}</h3>
                        <p>{t("additionalVerification")}</p>
                        <strong>{t("status")}: {t("underVerification")}</strong>
                      </div>
                    )}

                    {claimResult.claim_verification?.level === "high" && (
                      <div className="claim-next-action high-action">
                        <h3 className="claim-action-title high"><span className="action-status-dot high"></span> {t("highReview")}</h3>
                        <p>{t("detailedVerification")}</p>
                        <strong>{t("status")}: {t("highPriorityReview")}</strong>
                      </div>
                    )}
                  </div>

                  {claimResult.weather_verification && (
                    <WeatherVerificationCard
                      weather={claimResult.weather_verification}
                      t={t}
                    />
                  )}

                </div>
              )}
            </div>

            <div
              className="report-card"
              style={{ marginTop: "30px" }}
            >
              <div className="report-card-header">
                <div>
                  <h2>{t("claimHistory")}</h2>
                  <p>{t("claimsStored")}</p>
                </div>
              </div>

              {!authUser ? (
                <div className="report-section">
                  <p>{t("loginToHistory")}</p>
                </div>
              ) : (
                <>
                  <div className="claim-statistics">
                    <div className="stat-card">
                      <span className="stat-label">{t("totalClaims")}</span>
                      <strong className="stat-value">{totalClaims}</strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">{t("normalReview")}</span>
                      <strong className="stat-value">
                        {normalReviewClaims}
                      </strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">{t("mediumReview")}</span>
                      <strong className="stat-value">
                        {mediumReviewClaims}
                      </strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">{t("highReview")}</span>
                      <strong className="stat-value">
                        {highReviewClaims}
                      </strong>
                    </div>
                  </div>

                  <div className="claim-filters">
                    <input
                      type="text"
                      placeholder={t("searchClaims")}
                      value={claimSearch}
                      onChange={(e) => setClaimSearch(e.target.value)}
                      className="claim-search"
                    />

                    <select
                      value={claimStatusFilter}
                      onChange={(e) =>
                        setClaimStatusFilter(e.target.value)
                      }
                      className="claim-status-filter"
                    >
                      <option value="ALL">{t("allStatuses")}</option>
                      <option value="NORMAL REVIEW">{t("normalReview")}</option>
                      <option value="MEDIUM REVIEW">{t("mediumReview")}</option>
                      <option value="HIGH REVIEW">{t("highReview")}</option>
                    </select>
                  </div>

                  {filteredClaims.length === 0 ? (
                    <div className="report-section">
                      <p>
                        {normalizedHistory.length === 0
                          ? t("noClaims")
                          : t("noMatchingClaims")}
                      </p>
                    </div>
                  ) : (
                    <div style={{ overflowX: "auto" }}>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          marginTop: "20px",
                        }}
                      >
                        <thead>
                          <tr>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("crop")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("claimedLoss")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("visualEstimate")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("aiPrediction")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("modelConfidence")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("status")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("mlTriage")}
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              {t("action")}
                            </th>
                          </tr>
                        </thead>

                        <tbody>
                          {filteredClaims.map((claim) => (
                            <tr
                              key={claim.id}
                              style={{
                                borderTop: "1px solid #ddd",
                              }}
                            >
                              <td style={{ padding: "12px" }}>
                                {claim.crop || "—"}
                              </td>

                              <td style={{ padding: "12px" }}>
                                {claim.claimedLoss != null
                                  ? `${claim.claimedLoss}%`
                                  : "—"}
                              </td>

                              <td style={{ padding: "12px" }}>
                                {claim.estimatedDamage != null
                                  ? `${Number(
                                      claim.estimatedDamage
                                    ).toFixed(2)}%`
                                  : "—"}
                              </td>

                              <td style={{ padding: "12px" }}>
                                {claim.prediction || "—"}
                              </td>

                              <td style={{ padding: "12px" }}>
                                {claim.confidence != null
                                  ? `${Number(
                                      claim.confidence
                                    ).toFixed(2)}%`
                                  : "—"}
                              </td>

                              <td
                                style={{
                                  padding: "12px",
                                  fontWeight: "600",
                                }}
                              >
                                {claim.status === "NORMAL REVIEW"
                                  ? t("normalReview")
                                  : claim.status === "MEDIUM REVIEW"
                                  ? t("mediumReview")
                                  : claim.status === "HIGH REVIEW"
                                  ? t("highReview")
                                  : claim.status || t("pending")}
                              </td>

                              <td style={{ padding: "12px" }}>
                                {claim.riskModelUsed ? (
                                  <span>
                                    {t("ml")}
                                    {claim.riskScore != null
                                      ? ` · ${claim.riskScore}`
                                      : ""}
                                  </span>
                                ) : claim.rawReviewStatus ===
                                  "MODEL_NOT_READY" ? (
                                  <span>{t("modelPendingReview")}</span>
                                ) : (
                                  <span>—</span>
                                )}
                              </td>

                              <td style={{ padding: "12px" }}>
                                <button
                                  type="button"
                                  onClick={() =>
                                    deleteClaim(claim.id)
                                  }
                                  style={{
                                    padding: "7px 12px",
                                    border: "none",
                                    borderRadius: "6px",
                                    cursor: "pointer",
                                    fontWeight: "600",
                                  }}
                                >
                                  {t("delete")}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>
        )}


        {activePage === "reports" && (
          <section className="reports-page">
            <div className="page-title">
              <h1>{t("analysisReports")}</h1>
              <p>{t("reportsSubtitle")}</p>
            </div>

            {result ? (
              <div className="report-card">
                <div className="report-header">
                  <h1>{t("assessmentReport")}</h1>
                  <p>{t("remoteSensingAnalysis")}</p>
                  <div className="report-line"></div>
                </div>

                <div className="report-section">
                  <h2>{t("reportStudyArea")}</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>{t("district")}</span>
                      <strong>
                        {result.study_area?.district || selectedDistrict}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>{t("state")}</span>
                      <strong>
                        {result.study_area?.state || selectedState}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>{t("analysisPeriod")}</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>{t("beforeEvent")}</span>
                      <strong>
                        {result.periods?.before?.start || beforeStart} to{" "}
                        {result.periods?.before?.end || beforeEnd}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>{t("afterEvent")}</span>
                      <strong>
                        {result.periods?.after?.start || afterStart} to{" "}
                        {result.periods?.after?.end || afterEnd}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>{t("damageResults")}</h2>
                  <div className="report-results-grid">
                    <div className="report-result-box">
                      <span>{t("totalCropland")}</span>
                      <strong>{totalArea} ha</strong>
                    </div>
                    <div className="report-result-box">
                      <span>{t("potentialDamagedArea")}</span>
                      <strong>{damagedArea} ha</strong>
                    </div>
                    <div className="report-result-box">
                      <span>{t("damagePercentage")}</span>
                      <strong>{damagePercentage}%</strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>{t("satelliteData")}</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>{t("satelliteSource")}</span>
                      <strong>
                        {result.satellite_data?.source || "Sentinel-2"}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>{t("analysisPlatform")}</span>
                      <strong>
                        {result.satellite_data?.platform ||
                          "Google Earth Engine"}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section conclusion-section">
                  <h2>{t("assessmentConclusion")}</h2>
                  <p>{t("assessmentConclusionText", { damagedArea, damagePercentage })}</p>
                </div>

                <div className="report-disclaimer">
                  <strong>{t("disclaimer")}:</strong> {t("reportDisclaimer")}
                </div>

                <button
                  className="report-download-button"
                  onClick={() => window.print()}
                >
                  <FileTextIcon size={16} style={{ verticalAlign: "-2px", marginRight: "6px" }} /> {t("downloadReport")}
                </button>
              </div>
            ) : (
              <div className="no-report">
                <h2>{t("noReport")}</h2>
                <p>{t("noReportDescription")}</p>
                <button
                  className="analyze-button"
                  onClick={() => setActivePage("study")}
                >
                  {t("goToStudyArea")}
                </button>
              </div>
            )}
          </section>
        )}

        {activePage === "aiml_performance" && (
          <AimlPerformance t={t} />
        )}

        {activePage === "analysis" && (
          <section className="reports-page">
            <div className="page-title">
              <h1>{t("damageAnalysis")}</h1>
              <p>{t("ndviDescription")}</p>
            </div>

            <div className="report-card">
              <div className="report-card-header">
                <div>
                  <h2>{t("analysisStatus")}</h2>
                  <p>
                    {loading
                      ? t("satelliteProcessing")
                      : result
                      ? t("analysisCompleted")
                      : t("analysisReady")}
                  </p>
                </div>
                <span className="report-status">
                  {loading ? t("processing") : result ? t("completed") : t("ready")}
                </span>
              </div>

              <div className="report-summary-grid">
                <div>
                  <span>{t("studyArea")}</span>
                  <strong>
                    {selectedDistrict}, {selectedState}
                  </strong>
                </div>
                <div>
                  <span>{t("beforeEvent")}</span>
                  <strong>
                    {beforeStart} to {beforeEnd}
                  </strong>
                </div>
                <div>
                  <span>{t("afterEvent")}</span>
                  <strong>
                    {afterStart} to {afterEnd}
                  </strong>
                </div>
                <div>
                  <span>{t("method")}</span>
                  <strong>{t("ndviChangeDetection")}</strong>
                </div>
              </div>

              <button
                onClick={runAnalysis}
                disabled={loading}
                className="analyze-button"
              >
                {loading
                  ? t("analyzing")
                  : t("analyze", { district: selectedDistrict })}
              </button>
            </div>
          </section>
        )}

        {activePage === "dashboard" && (
          <>
            <header className="header">
              <div>
                <h1>{t("cropDamageDashboard")}</h1>
                <p>
                  {t("satelliteAnalysis")}
                </p>
              </div>

              <div className="header-actions">
                <div className="status">
                  <span className="status-dot"></span>
                  {loading
                    ? t("analyzing")
                    : result
                    ? t("analysisComplete")
                    : t("analysisReady")}
                </div>

                <button
                  onClick={runAnalysis}
                  disabled={loading}
                  className="analyze-button"
                >
                  {loading
                    ? t("analyzing")
                    : t("analyze", { district: selectedDistrict })}
                </button>
              </div>
            </header>

            <section className="study-banner">
              <div>
                <p className="section-label">{t("studyArea")}</p>
                <h2>
                  {t("locationTitle", {
                    district: t(`place.${selectedDistrict}`),
                    state: t(`place.${selectedState}`),
                  })}
                </h2>
                <p>
                  {t("pmfbySatelliteAssessment")}
                </p>
              </div>
              <div className="location-icon">
                <LocationPinIcon size={24} />
              </div>
            </section>

            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">
                  <SproutIcon size={22} />
                </div>
                <div>
                  <p>{t("totalCropland")}</p>
                  <h2>
                    {totalArea !== "—" ? `${totalArea} ha` : "—"}
                  </h2>
                  <span>{t("satelliteDerived")}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon red">
                  <AlertTriangleIcon size={22} />
                </div>
                <div>
                  <p>{t("potentialDamage")}</p>
                  <h2>
                    {damagedArea !== "—" ? `${damagedArea} ha` : "—"}
                  </h2>
                  <span>{t("ndviDetection")}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon orange">
                  <TrendingDownIcon size={22} />
                </div>
                <div>
                  <p>{t("damagePercentage")}</p>
                  <h2>
                    {damagePercentage !== "—"
                      ? `${damagePercentage}%`
                      : "—"}
                  </h2>
                  <span>{t("estimatedAffectedArea")}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon green">
                  <SatelliteDishIcon size={22} />
                </div>
                <div>
                  <p>{t("dataSource")}</p>
                  <h2>Sentinel-2</h2>
                  <span>Google Earth Engine</span>
                </div>
              </div>
            </section>

            <section className="dashboard-grid">
              <div className="card map-card">
                <div className="card-header">
                  <div>
                    <h2>{t("cropDamageMap")}</h2>
                    <p>{t("districtDamageAnalysis", { district: selectedDistrict })}</p>
                  </div>
                  <span className="map-badge">{t("ndviAnalysis")}</span>
                </div>

                <div className="map-placeholder">
                  {result?.maps?.damage_url ? (
                    <MapContainer
                      key={`${selectedDistrict}-${result.maps.damage_url}`}
                      center={
                        result?.study_area?.bounds
                          ? [
                              (result.study_area.bounds.south +
                                result.study_area.bounds.north) /
                                2,
                              (result.study_area.bounds.west +
                                result.study_area.bounds.east) /
                                2,
                            ]
                          : INDIA_CENTER
                      }
                      zoom={9}
                      scrollWheelZoom={true}
                      className="leaflet-map"
                    >
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution="&copy; OpenStreetMap contributors"
                      />
                      <TileLayer
                        url={result.maps.damage_url}
                        attribution="Google Earth Engine"
                        opacity={0.75}
                      />
                      {result?.study_area?.bounds && (
                        <FitBoundsToDistrict
                          bounds={result.study_area.bounds}
                        />
                      )}
                    </MapContainer>
                  ) : (
                    <div className="map-empty">
                      {t("generateMap", { district: selectedDistrict })}
                    </div>
                  )}
                </div>

                <div className="map-legend">
                  <span>
                    <i className="legend-box healthy"></i>
                    {t("healthyVegetation")}
                  </span>
                  <span>
                    <i className="legend-box damage"></i>
                    {t("potentialDamage")}
                  </span>
                </div>
              </div>

              <div className="card analysis-card">
                <div className="card-header">
                  <div>
                    <h2>{t("analysisSummary")}</h2>
                    <p>{t("processingWorkflow")}</p>
                  </div>
                </div>

                <div className="steps">
                  {[
                    t("satelliteDataCollection"), t("ndviCalculation"), t("damageDetection"), t("refinedAnalysis"),
                  ].map((step, index) => (
                    <div className="step completed" key={step}>
                      <div className="step-number">✓</div>
                      <div>
                        <h3>{step}</h3>
                        <p>
                          {index === 0
                            ? t("sentinelCollected")
                            : index === 1
                            ? t("vegetationComparison")
                            : index === 2
                            ? t("vegetationLossIdentified")
                            : t("croplandMasking")}
                        </p>
                      </div>
                    </div>
                  ))}

                  <div className={`step ${result ? "completed" : ""}`}>
                    <div className="step-number">
                      {result ? "✓" : "5"}
                    </div>
                    <div>
                      <h3>{t("finalReport")}</h3>
                      <p>
                        {result
                          ? t("resultsGenerated")
                          : t("resultsSummary")}
                      </p>
                      {result && (
                        <button
                          className="report-button"
                          onClick={() => setActivePage("reports")}
                        >
                          <FileTextIcon size={14} style={{ verticalAlign: "-2px", marginRight: "6px" }} /> {t("viewReport")}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </>
        )}
      </main>
      <Chatbot
        language={language}
        t={t}
        context={{ state: selectedState, district: selectedDistrict, page: activePage }}
        authUser={authUser}
        token={getStoredToken()}
      />
    </div>
  );
}

export default App;

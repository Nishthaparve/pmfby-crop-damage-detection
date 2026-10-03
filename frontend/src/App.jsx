import { useState, useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";
import Chatbot from "./Chatbot";
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

// ---- Login / Register form ----
function AuthForm({ mode, loading, error, onSubmit, t }) {
  const isLogin = mode === "login";
  const [values, setValues] = useState({
    name: "",
    phone: "",
    email: "",
    username: "",
    password: "",
    confirm_password: "",
    state: "Maharashtra",
    district: "Nagpur",
  });

  const set = (key) => (e) =>
    setValues((v) => ({ ...v, [key]: e.target.value }));

  const states = Object.keys(districtsByState);
  const districts = districtsByState[values.state] || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(values);
  };

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
  const [authMode, setAuthMode] = useState("login"); // "login" | "register"

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
            : "Failed to submit insurance claim.",
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
            : "Unable to delete claim."
        );
      }

      await loadClaims();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Unable to delete claim."
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
          <div className="logo-icon">🌾</div>
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
            <span>📊</span> {t("dashboard")}
          </button>

          <button
            className={`nav-item ${
              activePage === "analysis" ? "active" : ""
            }`}
            onClick={() => setActivePage("analysis")}
          >
            <span>🗺️</span> {t("damageAnalysis")}
          </button>

          <button
            className={`nav-item ${
              activePage === "study" ? "active" : ""
            }`}
            onClick={() => setActivePage("study")}
          >
            <span>📍</span> {t("studyArea")}
          </button>

          <button
            className={`nav-item ${
              activePage === "claim" ? "active" : ""
            }`}
            onClick={() => setActivePage("claim")}
          >
            <span>🛡️</span> {t("insuranceClaim")}
          </button>

          <button
            className={`nav-item ${
              activePage === "reports" ? "active" : ""
            }`}
            onClick={() => setActivePage("reports")}
          >
            <span>📄</span> {t("reports")}
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
              <span>🔐</span> {t("loginRegister")}
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
                ⎋
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
              <div className="auth-logo">🌾</div>
              <h1 className="auth-title">
                {authMode === "login" ? t("welcomeBack") : t("createAccount")}
              </h1>
              <p className="auth-subtitle">
                {authMode === "login"
                  ? t("loginSubtitle")
                  : t("registerSubtitle")}
              </p>

              <AuthForm
                mode={authMode}
                loading={authLoading}
                error={authError}
                t={t}
                onSubmit={async (values) => {
                  if (authMode === "login") {
                    await handleLogin(values.username, values.password);
                  } else {
                    await handleRegister(values);
                  }
                }}
              />

              <div className="auth-switch">
                {authMode === "login" ? (
                  <span>
                    {t("noAccount")} {" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("register");
                        setAuthError("");
                      }}
                    >
                      {t("register")}
                    </button>
                  </span>
                ) : (
                  <span>
                    {t("hasAccount")} {" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("login");
                        setAuthError("");
                      }}
                    >
                      {t("login")}
                    </button>
                  </span>
                )}
              </div>
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
                <div className="form-group">
                 <label>{t("farmPolygon")}</label>
                 <textarea value={farmPolygon} onChange={(e) => setFarmPolygon(e.target.value)} placeholder={t("polygonPlaceholder")} rows="3" />
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

                  {claimResult.evidence && (
                    <div className="evidence-panel">
                      <div className="evidence-panel-heading">
                        <div><h2>{t("supportingEvidence")}</h2><p>{t("supportingEvidenceDescription")}</p></div>
                        <strong className={`priority-pill ${claimResult.evidence.level}`}>{claimResult.evidence.priority_score}/100 · {claimResult.evidence.review_status}</strong>
                      </div>
                      <p className="human-review-note">{t("humanDecisionRequired")}</p>
                      <div className="evidence-list">
                        {(claimResult.evidence.factors || []).map((factor) => (
                          <div className="evidence-row" key={factor.source}>
                            <span className={factor.available ? "evidence-ready" : "evidence-pending"}>{factor.available ? t("available") : t("pending")}</span>
                            <span>{factor.label}</span><strong>{String(factor.value)}</strong>
                          </div>
                        ))}
                      </div>
                      <h3>{t("priorityExplanation")}</h3>
                      <ul>{(claimResult.evidence.explanations || []).map((item, index) => <li key={index}>{item}</li>)}</ul>
                      <p className="provider-status">{claimResult.evidence.provider_status}</p>
                    </div>
                  )}

                  <div className="report-section conclusion-section claim-risk-section">
                    <h2>{t("claimRisk")}</h2>
                    {claimResult.claim_verification?.model_used ? (
                      <>
                        {claimResult.claim_verification?.decision_type === "demo_ml" ? (
                          <p className="claim-risk-model"><strong>{t("researchDemo")}</strong></p>
                        ) : (
                          <p className="claim-risk-model"><strong>{t("trainedMlModel")}</strong></p>
                        )}
                        <p className="claim-risk-model">
                          <strong>{t("model")}:</strong>{" "}
                          {claimResult.claim_verification.model_name ||
                            "claim_risk_model"}
                        </p>
                        <p className="claim-risk-status">
                          <strong>{t("status")}:</strong>{" "}
                          {claimResult.claim_verification.review_status}
                        </p>
                        <p className="claim-risk-score">
                          <strong>{t("claimRiskScore")}:</strong>{" "}
                          {claimResult.claim_verification.claim_risk_score != null
                            ? `${(Number(claimResult.claim_verification.claim_risk_score) * 100).toFixed(1)}%`
                            : "—"}
                        </p>
                        <p className="human-review-note">
                          {claimResult.claim_verification?.decision_type === "demo_ml"
                            ? t("demoDisclaimer")
                            : t("trainedModelTriage")}
                          {" "}
                          {t("humanOfficerDecision")}
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="claim-risk-status">
                          <strong>{t("status")}:</strong> {t("modelNotReady")}
                        </p>
                        <p className="claim-risk-message">
                          {claimResult.claim_verification?.reason ||
                            claimResult.claim_verification?.message ||
                            t("awaitingVerifiedClaims")}
                        </p>
                        <p className="human-review-note">
                          {t("humanOfficerReview")}
                        </p>
                      </>
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
                        <h3>🟢 {t("normalReview")}</h3>
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
                        <h3>🟡 {t("mediumReview")}</h3>
                        <p>{t("additionalVerification")}</p>
                        <strong>{t("status")}: {t("underVerification")}</strong>
                      </div>
                    )}

                    {claimResult.claim_verification?.level === "high" && (
                      <div className="claim-next-action high-action">
                        <h3>🔴 {t("highReview")}</h3>
                        <p>{t("detailedVerification")}</p>
                        <strong>{t("status")}: {t("highPriorityReview")}</strong>
                      </div>
                    )}
                  </div>
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
                      placeholder={`🔍 ${t("searchClaims")}`}
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
                                    {claim.riskModel === "claim_risk_demo_model" ? t("demoMl") : t("ml")} · {claim.riskModel || "claim_risk_model"}{" "}
                                    · {claim.riskScore != null ? claim.riskScore : ""}
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
                  📄 {t("downloadReport")}
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
              <div className="location-icon">📍</div>
            </section>

            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">🌱</div>
                <div>
                  <p>{t("totalCropland")}</p>
                  <h2>
                    {totalArea !== "—" ? `${totalArea} ha` : "—"}
                  </h2>
                  <span>{t("satelliteDerived")}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon red">⚠️</div>
                <div>
                  <p>{t("potentialDamage")}</p>
                  <h2>
                    {damagedArea !== "—" ? `${damagedArea} ha` : "—"}
                  </h2>
                  <span>{t("ndviDetection")}</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon orange">📉</div>
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
                <div className="stat-icon green">🛰️</div>
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
                          📄 {t("viewReport")}
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
      <Chatbot language={language} t={t} context={{ state: selectedState, district: selectedDistrict, page: activePage }} />
    </div>
  );
}

export default App;

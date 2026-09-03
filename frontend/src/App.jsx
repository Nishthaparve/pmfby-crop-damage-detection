import { useState, useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";

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
function AuthForm({ mode, loading, error, onSubmit }) {
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
            <label>Full Name</label>
            <input
              type="text"
              value={values.name}
              onChange={set("name")}
              placeholder="Enter your full name"
              required
            />
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <input
              type="tel"
              value={values.phone}
              onChange={set("phone")}
              placeholder="10-digit mobile number"
              pattern="[6-9][0-9]{9}"
              required
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={values.email}
              onChange={set("email")}
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="auth-row">
            <div className="form-group">
              <label>State</label>
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
              <label>District</label>
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
        <label>Username</label>
        <input
          type="text"
          value={values.username}
          onChange={set("username")}
          placeholder="Choose a username"
          required
        />
      </div>

      <div className="form-group">
        <label>Password</label>
        <input
          type="password"
          value={values.password}
          onChange={set("password")}
          placeholder="At least 6 characters"
          required
        />
      </div>

      {!isLogin && (
        <div className="form-group">
          <label>Confirm Password</label>
          <input
            type="password"
            value={values.confirm_password}
            onChange={set("confirm_password")}
            placeholder="Re-enter your password"
            required
          />
        </div>
      )}

      {error && <div className="auth-error">{error}</div>}

      <button type="submit" className="analyze-button" disabled={loading}>
        {loading
          ? isLogin
            ? "Logging in..."
            : "Registering..."
          : isLogin
          ? "Login"
          : "Register"}
      </button>
    </form>
  );
}

function App() {
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
            : "Failed to load insurance claims."
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
            : "Login failed. Please try again."
        );
      }
      storeToken(data.token);
      setAuthUser(data.user);
      setActivePage("dashboard");
      await loadClaims();
    } catch (error) {
      setAuthError(error.message || "Login failed.");
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
            : "Registration failed. Please try again."
        );
      }
      storeToken(data.token);
      setAuthUser(data.user);
      setActivePage("dashboard");
      await loadClaims();
    } catch (error) {
      setAuthError(error.message || "Registration failed.");
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
      setProfileError("Please fill in all fields.");
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
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to update profile."
        );
      }

      // The username may have changed, so re-issue token is stored too.
      if (data.token) storeToken(data.token);
      setAuthUser(data.user);
      setProfileEditMode(false);
      setProfileForm(null);
    } catch (error) {
      setProfileError(error.message || "Failed to update profile.");
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
      alert("Please login or register to use this feature.");
      setAuthMode("login");
      setActivePage("auth");
      return;
    }

    if (!selectedState || !selectedDistrict) {
      alert("Please select both State and District.");
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
      alert(`Analysis failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  const submitClaim = async () => {
    if (!authUser) {
      alert("Please login or register to use this feature.");
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
      alert("Please complete all claim fields and upload a crop image.");
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

      const upperStatus = String(reviewStatus)
        .trim()
        .toUpperCase();

      const level =
        upperStatus.includes("NORMAL")
          ? "normal"
          : upperStatus.includes("MEDIUM")
          ? "medium"
          : upperStatus.includes("HIGH")
          ? "high"
          : null;

      setClaimResult({
        ...data,
        claim_verification: {
          ...(data.claim_verification || {}),
          review_status: reviewStatus,
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
      alert("Please login or register to use this feature.");
      setAuthMode("login");
      setActivePage("auth");
      return;
    }

    if (
      !window.confirm(
        "Are you sure you want to delete this claim from history?"
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
            <span>Crop Damage Detection</span>
          </div>
        </div>

        <nav className="nav-menu">
          <button
            className={`nav-item ${
              activePage === "dashboard" ? "active" : ""
            }`}
            onClick={() => setActivePage("dashboard")}
          >
            <span>📊</span> Dashboard
          </button>

          <button
            className={`nav-item ${
              activePage === "analysis" ? "active" : ""
            }`}
            onClick={() => setActivePage("analysis")}
          >
            <span>🗺️</span> Damage Analysis
          </button>

          <button
            className={`nav-item ${
              activePage === "study" ? "active" : ""
            }`}
            onClick={() => setActivePage("study")}
          >
            <span>📍</span> Study Area
          </button>

          <button
            className={`nav-item ${
              activePage === "claim" ? "active" : ""
            }`}
            onClick={() => setActivePage("claim")}
          >
            <span>🛡️</span> Insurance Claim
          </button>

          <button
            className={`nav-item ${
              activePage === "reports" ? "active" : ""
            }`}
            onClick={() => setActivePage("reports")}
          >
            <span>📄</span> Reports
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
              <span>🔐</span> Login / Register
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
              title="View profile"
            >
              <div className="user-avatar">
                {String(authUser.name || authUser.username || "U")
                  .charAt(0)
                  .toUpperCase()}
              </div>
              <div className="user-meta">
                <strong>{authUser.name || authUser.username}</strong>
                <span>
                  {authUser.district}, {authUser.state}
                </span>
              </div>
              <button
                className="user-logout"
                onClick={(e) => {
                  e.stopPropagation();
                  handleLogout();
                }}
                title="Logout"
              >
                ⎋
              </button>
            </div>
          ) : (
            <>
              <p>PMFBY Project</p>
              <span>AI & Remote Sensing Based</span>
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
                {authMode === "login" ? "Welcome Back" : "Create Account"}
              </h1>
              <p className="auth-subtitle">
                {authMode === "login"
                  ? "Login to access PMFBY Crop Damage Detection"
                  : "Register to start analyzing crop damage"}
              </p>

              <AuthForm
                mode={authMode}
                loading={authLoading}
                error={authError}
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
                    Don't have an account?{" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("register");
                        setAuthError("");
                      }}
                    >
                      Register
                    </button>
                  </span>
                ) : (
                  <span>
                    Already have an account?{" "}
                    <button
                      className="auth-link"
                      onClick={() => {
                        setAuthMode("login");
                        setAuthError("");
                      }}
                    >
                      Login
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
                  <h1>My Profile</h1>
                  <p>Your PMFBY account details</p>
                </div>

                <div className="study-form-card">
                  {!profileEditMode ? (
                    <>
                      <div className="form-group">
                        <label>Name</label>
                        <input
                          type="text"
                          value={authUser.name || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>Username</label>
                        <input
                          type="text"
                          value={authUser.username || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>Email</label>
                        <input
                          type="text"
                          value={authUser.email || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>Phone</label>
                        <input
                          type="text"
                          value={authUser.phone || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>State</label>
                        <input
                          type="text"
                          value={authUser.state || ""}
                          readOnly
                        />
                      </div>

                      <div className="form-group">
                        <label>District</label>
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
                        Edit Profile
                      </button>

                      <button
                        className="analyze-button"
                        style={{ marginTop: "10px" }}
                        onClick={handleLogout}
                      >
                        Logout
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="form-group">
                        <label>Name</label>
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
                        <label>Username</label>
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
                        <label>Email</label>
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
                        <label>Phone</label>
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
                          <label>State</label>
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
                          <label>District</label>
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
                        {profileSaving ? "Saving..." : "Save Changes"}
                      </button>

                      <button
                        className="analyze-button"
                        style={{ marginTop: "10px" }}
                        onClick={cancelEditProfile}
                        disabled={profileSaving}
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="page-title">
                <h1>My Profile</h1>
                <p>Please login or register to view your profile.</p>
              </div>
            )}
          </section>
        )}

        {activePage === "study" && (
          <section className="study-page">
            <div className="page-title">
              <h1>Select Study Area</h1>
              <p>
                Choose the location and time period for crop damage analysis
              </p>
            </div>

            <div className="study-form-card">
              <div className="form-group">
                <label>Select State</label>
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
                <label>Select District</label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  disabled={
                    !selectedState || availableDistricts.length === 0
                  }
                >
                  <option value="">Select District</option>
                  {availableDistricts.map((district) => (
                    <option key={district} value={district}>
                      {district}
                    </option>
                  ))}
                </select>
              </div>

              <h3>Before Event Period</h3>

              <div className="date-grid">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={beforeStart}
                    onChange={(e) => setBeforeStart(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    value={beforeEnd}
                    onChange={(e) => setBeforeEnd(e.target.value)}
                  />
                </div>
              </div>

              <h3>After Event Period</h3>

              <div className="date-grid">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={afterStart}
                    onChange={(e) => setAfterStart(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>End Date</label>
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
                  ? "Analyzing..."
                  : `Analyze ${selectedDistrict || "Study Area"}`}
              </button>
            </div>
          </section>
        )}

        {activePage === "claim" && (
          <section className="study-page">
            <div className="page-title">
              <h1>Submit Insurance Claim</h1>
              <p>
                Submit your claim directly for AI-assisted image analysis.
              </p>
            </div>

            <div className="study-form-card">
              <h3>Farmer Claim Details</h3>

              <div className="form-group">
                <label>Crop Name</label>
                <input
                  type="text"
                  value={claimCrop}
                  onChange={(e) => setClaimCrop(e.target.value)}
                  placeholder="Example: Grape, Apple, Tomato"
                />
              </div>

              <div className="form-group">
                <label>Claimed Crop Loss (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={claimedLoss}
                  onChange={(e) => setClaimedLoss(e.target.value)}
                  placeholder="Example: 40"
                />
              </div>

              <div className="form-group">
                <label>Farm Area (Acres)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={farmArea}
                  onChange={(e) => setFarmArea(e.target.value)}
                  placeholder="Example: 2.5"
                />
              </div>

              <div className="form-group">
                <label>Farm Location / Village</label>
                <input
                  type="text"
                  value={claimLocation}
                  onChange={(e) => setClaimLocation(e.target.value)}
                  placeholder="Enter village or farm location"
                />
              </div>

              <div className="form-group">
                <label>State</label>
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
                <label>District</label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  disabled={!selectedState || availableDistricts.length === 0}
                >
                  <option value="">Select District</option>
                  {availableDistricts.map((district) => (
                    <option key={district} value={district}>
                      {district}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Upload Crop Damage Image</label>
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={(e) =>
                    setClaimImage(e.target.files?.[0] || null)
                  }
                />

                {claimImage && (
                  <p style={{ marginTop: "10px" }}>
                    Selected image: <strong>{claimImage.name}</strong>
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
                  ? "AI is Verifying Claim..."
                  : "Submit Claim for Verification"}
              </button>

              {claimResult?.status === "error" && (
                <div
                  className="report-card"
                  style={{ marginTop: "30px" }}
                >
                  <div className="report-section conclusion-section">
                    <h2>Claim Submission Error</h2>
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
                      <h2>AI Claim Verification Result</h2>
                      <p>
                        Actual trained-model prediction from the uploaded image
                      </p>
                    </div>

                    <span className="report-status">
                      {claimResult.claim_verification?.review_status ||
                        "PENDING"}
                    </span>
                  </div>

                  <div className="report-results-grid">
                    <div className="report-result-box">
                      <span>Farmer Claimed Loss</span>
                      <strong>
                        {claimResult.farmer_claim
                          ?.claimed_loss_percentage ?? claimedLoss}
                        %
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>AI Disease Prediction</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.predicted_crop_disease ||
                          "Prediction unavailable"}
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>Model Confidence</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.model_confidence != null
                          ? `${Number(
                              claimResult.image_analysis.model_confidence
                            ).toFixed(2)}%`
                          : "Unavailable"}
                      </strong>
                    </div>

                    <div className="report-result-box">
                      <span>AI Estimated Damage</span>
                      <strong>
                        {claimResult.image_analysis
                          ?.estimated_damage_percentage != null
                          ? `${Number(
                              claimResult.image_analysis
                                .estimated_damage_percentage
                            ).toFixed(2)}%`
                          : "Not available"}
                      </strong>
                    </div>
                  </div>

                  <div className="report-section conclusion-section">
                    <h2>Review Decision</h2>

                    <p>
                      {claimResult.claim_verification?.reason ||
                        "No review reason returned."}
                    </p>

                    {claimResult.claim_verification?.level === "normal" && (
                      <div className="claim-next-action normal-action">
                        <h3>🟢 Normal Review</h3>
                        <p>
                          Your claim can continue through the normal PMFBY
                          process.
                        </p>

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
                          Continue to Official PMFBY Portal →
                        </a>
                      </div>
                    )}

                    {claimResult.claim_verification?.level === "medium" && (
                      <div className="claim-next-action medium-action">
                        <h3>🟡 Medium Review</h3>
                        <p>
                          Additional verification is required before the claim
                          proceeds.
                        </p>
                        <strong>Status: Under Verification</strong>
                      </div>
                    )}

                    {claimResult.claim_verification?.level === "high" && (
                      <div className="claim-next-action high-action">
                        <h3>🔴 High Review</h3>
                        <p>
                          Detailed manual verification is required before the
                          claim proceeds.
                        </p>
                        <strong>
                          Status: High-Priority Manual Review Required
                        </strong>
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
                  <h2>Insurance Claim History</h2>
                  <p>Claims stored in the backend database</p>
                </div>
              </div>

              {!authUser ? (
                <div className="report-section">
                  <p>Please login or register to view your claim history.</p>
                </div>
              ) : (
                <>
                  <div className="claim-statistics">
                    <div className="stat-card">
                      <span className="stat-label">Total Claims</span>
                      <strong className="stat-value">{totalClaims}</strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">Normal Review</span>
                      <strong className="stat-value">
                        {normalReviewClaims}
                      </strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">Medium Review</span>
                      <strong className="stat-value">
                        {mediumReviewClaims}
                      </strong>
                    </div>

                    <div className="stat-card">
                      <span className="stat-label">High Review</span>
                      <strong className="stat-value">
                        {highReviewClaims}
                      </strong>
                    </div>
                  </div>

                  <div className="claim-filters">
                    <input
                      type="text"
                      placeholder="🔍 Search by crop, location, district, state, or disease..."
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
                      <option value="ALL">All Statuses</option>
                      <option value="NORMAL REVIEW">Normal Review</option>
                      <option value="MEDIUM REVIEW">Medium Review</option>
                      <option value="HIGH REVIEW">High Review</option>
                    </select>
                  </div>

                  {filteredClaims.length === 0 ? (
                    <div className="report-section">
                      <p>
                        {normalizedHistory.length === 0
                          ? "No insurance claims have been submitted yet."
                          : "No claims match your search or selected status."}
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
                              Crop
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              Claimed Loss
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              AI Damage
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              AI Prediction
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              Confidence
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              Status
                            </th>
                            <th style={{ padding: "12px", textAlign: "left" }}>
                              Action
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
                                {claim.status || "PENDING"}
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
                                  Delete
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
              <h1>Analysis Reports</h1>
              <p>View and download crop damage assessment reports</p>
            </div>

            {result ? (
              <div className="report-card">
                <div className="report-header">
                  <h1>PMFBY Crop Damage Assessment Report</h1>
                  <p>AI & Remote Sensing Based Crop Damage Analysis</p>
                  <div className="report-line"></div>
                </div>

                <div className="report-section">
                  <h2>1. Study Area</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>District</span>
                      <strong>
                        {result.study_area?.district || selectedDistrict}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>State</span>
                      <strong>
                        {result.study_area?.state || selectedState}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>2. Analysis Period</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>Before Event</span>
                      <strong>
                        {result.periods?.before?.start || beforeStart} to{" "}
                        {result.periods?.before?.end || beforeEnd}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>After Event</span>
                      <strong>
                        {result.periods?.after?.start || afterStart} to{" "}
                        {result.periods?.after?.end || afterEnd}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>3. Crop Damage Analysis Results</h2>
                  <div className="report-results-grid">
                    <div className="report-result-box">
                      <span>Total Cropland</span>
                      <strong>{totalArea} ha</strong>
                    </div>
                    <div className="report-result-box">
                      <span>Potential Damaged Area</span>
                      <strong>{damagedArea} ha</strong>
                    </div>
                    <div className="report-result-box">
                      <span>Damage Percentage</span>
                      <strong>{damagePercentage}%</strong>
                    </div>
                  </div>
                </div>

                <div className="report-section">
                  <h2>4. Satellite Data</h2>
                  <div className="report-info-grid">
                    <div className="report-info-item">
                      <span>Satellite Source</span>
                      <strong>
                        {result.satellite_data?.source || "Sentinel-2"}
                      </strong>
                    </div>
                    <div className="report-info-item">
                      <span>Analysis Platform</span>
                      <strong>
                        {result.satellite_data?.platform ||
                          "Google Earth Engine"}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="report-section conclusion-section">
                  <h2>5. Assessment Conclusion</h2>
                  <p>
                    The analysis identified approximately{" "}
                    <strong>{damagedArea} hectares</strong> of potential crop
                    damage, representing{" "}
                    <strong>{damagePercentage}%</strong> of the analyzed
                    cropland area.
                  </p>
                </div>

                <div className="report-disclaimer">
                  <strong>Disclaimer:</strong> Results represent potential
                  vegetation loss based on satellite-derived analysis and
                  should be verified through field assessment before final
                  insurance decisions.
                </div>

                <button
                  className="report-download-button"
                  onClick={() => window.print()}
                >
                  📄 Download Report
                </button>
              </div>
            ) : (
              <div className="no-report">
                <h2>No Analysis Report Yet</h2>
                <p>
                  Run the crop damage analysis first to generate a report.
                </p>
                <button
                  className="analyze-button"
                  onClick={() => setActivePage("study")}
                >
                  Go to Study Area
                </button>
              </div>
            )}
          </section>
        )}

        {activePage === "analysis" && (
          <section className="reports-page">
            <div className="page-title">
              <h1>Damage Analysis</h1>
              <p>
                NDVI-based crop damage assessment using Sentinel-2 satellite
                imagery
              </p>
            </div>

            <div className="report-card">
              <div className="report-card-header">
                <div>
                  <h2>Analysis Status</h2>
                  <p>
                    {loading
                      ? "Satellite data is being processed..."
                      : result
                      ? "Analysis completed successfully"
                      : "Ready to start analysis"}
                  </p>
                </div>
                <span className="report-status">
                  {loading ? "Processing" : result ? "Completed" : "Ready"}
                </span>
              </div>

              <div className="report-summary-grid">
                <div>
                  <span>Study Area</span>
                  <strong>
                    {selectedDistrict}, {selectedState}
                  </strong>
                </div>
                <div>
                  <span>Before Event</span>
                  <strong>
                    {beforeStart} to {beforeEnd}
                  </strong>
                </div>
                <div>
                  <span>After Event</span>
                  <strong>
                    {afterStart} to {afterEnd}
                  </strong>
                </div>
                <div>
                  <span>Method</span>
                  <strong>NDVI Change Detection</strong>
                </div>
              </div>

              <button
                onClick={runAnalysis}
                disabled={loading}
                className="analyze-button"
              >
                {loading
                  ? "Analyzing..."
                  : `Analyze ${selectedDistrict}`}
              </button>
            </div>
          </section>
        )}

        {activePage === "dashboard" && (
          <>
            <header className="header">
              <div>
                <h1>Crop Damage Detection Dashboard</h1>
                <p>
                  Satellite-based analysis for identifying potential crop damage
                </p>
              </div>

              <div className="header-actions">
                <div className="status">
                  <span className="status-dot"></span>
                  {loading
                    ? "Analyzing..."
                    : result
                    ? "Analysis Complete"
                    : "Analysis Ready"}
                </div>

                <button
                  onClick={runAnalysis}
                  disabled={loading}
                  className="analyze-button"
                >
                  {loading
                    ? "Analyzing..."
                    : `Analyze ${selectedDistrict}`}
                </button>
              </div>
            </header>

            <section className="study-banner">
              <div>
                <p className="section-label">STUDY AREA</p>
                <h2>
                  {selectedDistrict} District, {selectedState}
                </h2>
                <p>
                  PMFBY Crop Damage Assessment using Sentinel-2 Satellite Data
                </p>
              </div>
              <div className="location-icon">📍</div>
            </section>

            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">🌱</div>
                <div>
                  <p>Total Cropland</p>
                  <h2>
                    {totalArea !== "—" ? `${totalArea} ha` : "—"}
                  </h2>
                  <span>Satellite derived</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon red">⚠️</div>
                <div>
                  <p>Potential Damage</p>
                  <h2>
                    {damagedArea !== "—" ? `${damagedArea} ha` : "—"}
                  </h2>
                  <span>NDVI based detection</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon orange">📉</div>
                <div>
                  <p>Damage Percentage</p>
                  <h2>
                    {damagePercentage !== "—"
                      ? `${damagePercentage}%`
                      : "—"}
                  </h2>
                  <span>Estimated affected area</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon green">🛰️</div>
                <div>
                  <p>Data Source</p>
                  <h2>Sentinel-2</h2>
                  <span>Google Earth Engine</span>
                </div>
              </div>
            </section>

            <section className="dashboard-grid">
              <div className="card map-card">
                <div className="card-header">
                  <div>
                    <h2>Crop Damage Map</h2>
                    <p>{selectedDistrict} crop damage analysis</p>
                  </div>
                  <span className="map-badge">NDVI Analysis</span>
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
                      {`Click "Analyze ${selectedDistrict}" to generate the crop damage map`}
                    </div>
                  )}
                </div>

                <div className="map-legend">
                  <span>
                    <i className="legend-box healthy"></i>
                    Healthy Vegetation
                  </span>
                  <span>
                    <i className="legend-box damage"></i>
                    Potential Damage
                  </span>
                </div>
              </div>

              <div className="card analysis-card">
                <div className="card-header">
                  <div>
                    <h2>Analysis Summary</h2>
                    <p>Current processing workflow</p>
                  </div>
                </div>

                <div className="steps">
                  {[
                    "Satellite Data Collection",
                    "NDVI Calculation",
                    "Damage Detection",
                    "Refined Analysis",
                  ].map((step, index) => (
                    <div className="step completed" key={step}>
                      <div className="step-number">✓</div>
                      <div>
                        <h3>{step}</h3>
                        <p>
                          {index === 0
                            ? "Sentinel-2 images collected"
                            : index === 1
                            ? "Before and after vegetation comparison"
                            : index === 2
                            ? "Potential vegetation loss identified"
                            : "Cropland masking and noise reduction"}
                        </p>
                      </div>
                    </div>
                  ))}

                  <div className={`step ${result ? "completed" : ""}`}>
                    <div className="step-number">
                      {result ? "✓" : "5"}
                    </div>
                    <div>
                      <h3>Final Report</h3>
                      <p>
                        {result
                          ? "Results and damage summary generated"
                          : "Results and damage summary"}
                      </p>
                      {result && (
                        <button
                          className="report-button"
                          onClick={() => setActivePage("reports")}
                        >
                          📄 View Report
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
    </div>
  );
}

export default App;
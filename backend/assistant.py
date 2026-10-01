# -*- coding: utf-8 -*-
"""
PMFBY Crop Damage Detection & Claim Verification - Assistant Chatbot Backend
Features:
1. Fast local intent matching (<5ms) for website navigation and project FAQs.
2. 100% project-specific answers (strictly NO external pmfby.gov.in / CSC / government portal mentions).
3. Context-aware login status handling (logged-in vs guest farmer).
4. Robust 12-language multilingual support (en, hi, mr, ta, te, bn, gu, kn, ml, pa, as, or).
5. Fast Gemini generation with active working models (gemini-3-flash-preview, gemini-3.1-flash-lite-preview) and 8s timeout.
"""
import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import Header
from jose import jwt, JWTError
import urllib.request
import urllib.error

# Resolve base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "claims.db"
SECRET_KEY = "pmfby-crop-damage-secret-key-change-in-production"
ALGORITHM = "HS256"

# Supported language codes
SUPPORTED_LANGUAGES = {"en", "hi", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa", "as", "or"}

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "as": "Assamese",
    "or": "Odia"
}

# Localized "Please login to use this feature."
LOGIN_REQUIRED_MESSAGES = {
    "en": "Please log in to view your personal claims and account details. You can log in via 'Login / Register' in the left sidebar.",
    "hi": "अपने व्यक्तिगत दावों और खाते की जानकारी देखने के लिए कृपया लॉगिन करें। आप बाईं साइडबार में 'Login / Register' से लॉगिन कर सकते हैं।",
    "mr": "तुमचे वैयक्तिक दावे आणि खात्याची माहिती पाहण्यासाठी कृपया डाव्या साइडबारमधील 'Login / Register' द्वारे लॉग इन करा.",
    "ta": "உங்கள் தனிப்பட்ட கோரிக்கைகள் மற்றும் கணக்கு விவரங்களைக் காண உள்நுழையவும். இடது மெனுவில் 'Login / Register' மூலம் உள்நுழையலாம்.",
    "te": "మీ వ్యక్తిగత క్లెయిమ్‌లు మరియు ఖాతా వివరాలను చూడటానికి దయచేసి లాగిన్ చేయండి. ఎడమ సైడ్‌బార్‌లోని 'Login / Register' ద్వారా లాగిన్ చేయవచ్చు.",
    "bn": "আপনার ব্যক্তিগত দাবি ও অ্যাকাউন্টের বিবরণ দেখতে অনুগ্রহ করে লগইন করুন। বাম সাইডবারের 'Login / Register' থেকে লগইন করতে পারেন।",
    "gu": "તમારા વ્યક્તિગત દાવાઓ અને ખાતાની વિગતો જોવા માટે કૃપા કરીને લૉગિન કરો. ડાબી બાજુના સાઇડબારમાં 'Login / Register' થી લૉગિન કરી શકો છો.",
    "kn": "ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಹಕ್ಕುಗಳು ಮತ್ತು ಖಾತೆಯ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಲು ದಯವಿಟ್ಟು ಲಾಗಿನ್ ಮಾಡಿ. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Login / Register' ಮೂಲಕ ಲಾಗಿನ್ ಮಾಡಬಹುದು.",
    "ml": "നിങ്ങളുടെ വ്യക്തിഗത ക്ലെയിമുകളും അക്കൗണ്ട് വിവരങ്ങളും കാണാൻ ദയവായി ലോഗിൻ ചെയ്യുക. ഇടത് സൈഡ്ബാറിലെ 'Login / Register' വഴി ലോഗിൻ ചെയ്യാം.",
    "pa": "ਆਪਣੇ ਨਿੱਜੀ ਦਾਅਵੇ ਅਤੇ ਖਾਤੇ ਦੇ ਵੇਰਵੇ ਦੇਖਣ ਲਈ ਕਿਰਪਾ ਕਰਕੇ ਲੌਗਇਨ ਕਰੋ। ਖੱਬੇ ਪਾਸੇ 'Login / Register' ਰਾਹੀਂ ਲੌਗਇਨ ਕਰ ਸਕਦੇ ਹੋ।",
    "as": "আপোনাৰ ব্যক্তিগত দাবী আৰু একাউণ্টৰ তথ্য চাবলৈ অনুগ্ৰহ কৰি লগইন কৰক। বাওঁফালৰ ছাইডবাৰত 'Login / Register' ৰ জৰিয়তে লগইন কৰিব পাৰে।",
    "or": "ଆପଣଙ୍କ ବ୍ୟକ୍ତିଗତ ଦାବି ଏବଂ ଖାତା ବିବରଣୀ ଦେଖିବା ପାଇଁ ଦୟାକରି ଲଗଇନ କରନ୍ତୁ। ବାମ ପାର୍ଶ୍ୱରେ ଥିବା 'Login / Register' ଦ୍ୱାରା ଲଗଇନ କରିପାରିବେ।"
}

# Personal patterns for identifying logged-out users asking for their private personal account data
PERSONAL_PATTERNS = [
    r"\bmy\s+payout\b", r"\bmy\s+application\b", r"\bmy\s+account\b", r"\bdelete\s+my\b",
    r"मेरा\s*खाता", r"माझे\s*खाते", r"என்\s*கணக்கு", r"నా\s*ఖాతా", r"আমার\s*অ্যাকাউন্ট",
    r"મારું\s*ખાતું", r"ನನ್ನ\s*ಖಾತೆ", r"എന്റെ\s*അക്കൗണ്ട്", r"ਮੇਰਾ\s*ਖਾਤਾ", r"মোৰ\s*একাউণ্ট", r"ମୋ\s*ଖାତା"
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_env_gemini_key() -> Optional[str]:
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    env_paths = [BASE_DIR / ".env", BASE_DIR / "backend" / ".env", Path(".env")]
    for p in env_paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GEMINI_API_KEY":
                            val = v.strip().strip("'\"")
                            if val:
                                return val
            except Exception:
                pass
    return None

def get_optional_user_from_header(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    if not authorization or not isinstance(authorization, str) or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
        user = cursor.fetchone()
        conn.close()
        if user:
            return dict(user)
        return None
    except Exception:
        return None

def is_personal_query(message: str) -> bool:
    msg = (message or "").lower()
    for pattern in PERSONAL_PATTERNS:
        if re.search(pattern, msg, re.IGNORECASE):
            return True
    return False

def get_user_claims_summary(user_id: int, language: str) -> str:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop, claimed_loss, review_status, created_at FROM claims WHERE user_id = ? ORDER BY id DESC LIMIT 3",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        count = len(rows)
        if count == 0:
            summaries = {
                "en": "You have not submitted any insurance claims yet on this website. You can submit one from the 'Insurance Claim' page in the left sidebar.",
                "hi": "आपने अभी तक इस वेबसाइट पर कोई बीमा दावा जमा नहीं किया है। आप बाईं साइडबार में 'Insurance Claim' (बीमा दावा) पृष्ठ से नया दावा जमा कर सकते हैं।",
                "mr": "तुम्ही अजून या वेबसाइटवर कोणताही विमा दावा सादर केलेला नाही. तुम्ही डाव्या बाजूच्या साइडबारमधील 'Insurance Claim' पृष्ठावरून नवीन दावा सादर करू शकता.",
                "ta": "நீங்கள் இதுவரை இந்த இணையதளத்தில் எந்த காப்பீட்டு கோரிக்கையையும் சமர்ப்பிக்கவில்லை. இடது மெனுவில் 'Insurance Claim' பக்கத்திலிருந்து புதிய கோரிக்கையை சமர்ப்பிக்கலாம்.",
                "te": "మీరు ఇప్పటివరకు ఈ వెబ్‌సైట్‌లో ఎటువంటి బీమా క్లెయిమ్‌ను సమర్పించలేదు. మీరు ఎడమ సైడ్‌బార్‌లోని 'Insurance Claim' పేజీ నుండి కొత్త క్లెయిమ్‌ను సమర్పించవచ్చు.",
                "bn": "আপনি এখনও এই ওয়েবসাইটে কোনো বিমা দাবি জমা দেননি। আপনি বাম সাইডবারে 'Insurance Claim' পৃষ্ঠা থেকে নতুন দাবি জমা দিতে পারেন।",
                "gu": "તમે હજુ સુધી આ વેબસાઇટ પર કોઈ વીમા દાવો સબમિટ કર્યો નથી. તમે ડાબી બાજુના સાઇડબારમાં 'Insurance Claim' પૃષ્ઠ પરથી નવો દાવો સબમિટ કરી શકો છો.",
                "kn": "ನೀವು ಇನ್ನೂ ಈ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ವಿಮಾ ಹಕ್ಕನ್ನು ಸಲ್ಲಿಸಿಲ್ಲ. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನ 'Insurance Claim' ಪುಟದಿಂದ ಹೊಸ ಹಕ್ಕನ್ನು ಸಲ್ಲಿಸಬಹುದು.",
                "ml": "നിങ്ങൾ ഇതുവരെ ഈ വെബ്സൈറ്റിൽ ഇൻഷുറൻസ് ക്ലെയിം ഒന്നും സമർപ്പിച്ചിട്ടില്ല. ഇടത് സൈഡ്ബാറിലെ 'Insurance Claim' പേജിൽ നിന്ന് പുതിയത് സമർപ്പിക്കാം.",
                "pa": "ਤੁਸੀਂ ਅਜੇ ਤੱਕ ਇਸ ਵੈੱਬਸਾਈਟ 'ਤੇ ਕੋਈ ਬੀਮਾ ਦਾਅਵਾ ਪੇਸ਼ ਨਹੀਂ ਕੀਤਾ ਹੈ। ਤੁਸੀਂ ਖੱਬੇ ਪਾਸੇ 'Insurance Claim' ਪੰਨੇ ਤੋਂ ਨਵਾਂ ਦਾਅਵਾ ਦਰਜ ਕਰ ਸਕਦੇ ਹੋ।",
                "as": "আপুনি এতিয়ালৈকে এই ৱেবছাইটত কোনো বীমা দাবী দাখিল কৰা নাই। আপুনি বাওঁফালৰ ছাইডবাৰত 'Insurance Claim' পৃষ্ঠাৰ পৰা নতুন দাবী দাখিল কৰিব পাৰে।",
                "or": "ଆପଣ ଏପର୍ଯ୍ୟନ୍ତ ଏହି ୱେବସାଇଟରେ କୌଣସି ବୀମା ଦାବି ଦାଖଲ କରିନାହାଁନ୍ତି। ଆପଣ ବାମ ପାର୍ଶ୍ୱରେ 'Insurance Claim' ପୃଷ୍ଠାରୁ ନୂଆ ଦାବି ଦାଖଲ କରିପାରିବେ।"
            }
            return summaries.get(language, summaries["en"])

        latest = rows[0]
        crop = latest["crop"]
        status = latest["review_status"] or "PENDING"
        summaries = {
            "en": f"You have {count} claim(s) recorded on this website. Your latest claim for {crop} is currently at: {status}. Note: A human PMFBY officer reviews this evidence before final decision. To see all your claims and AI verification data, click 'Reports' in the left sidebar.",
            "hi": f"इस वेबसाइट पर आपके {count} दावा(दावे) दर्ज हैं। {crop} के लिए आपका नवीनतम दावा स्थिति: {status} में है। ध्यान दें: अंतिम निर्णय अधिकृत मानव अधिकारी द्वारा लिया जाता है। अपने सभी दावों और AI साक्ष्य को देखने के लिए बाईं साइडबार में 'Reports' पर क्लिक करें।",
            "mr": f"या वेबसाइटवर तुमचे {count} दावा(दावे) नोंदवले आहेत. {crop} पिकासाठीचा तुमचा नवीनतम दावा स्थिती: {status} आहे. टीप: अंतिम निर्णय अधिकृत मानवी अधिकारी घेतात. तुमचे सर्व दावे आणि AI पुरावे पाहण्यासाठी डाव्या बाजूच्या साइडबारमध्ये 'Reports' वर क्लिक करा.",
            "ta": f"இந்த இணையதளத்தில் உங்கள் {count} கோரிக்கைகள் உள்ளன. {crop} பயிருக்கான சமீபத்திய நிலை: {status}. குறிப்பு: இறுதி முடிவை மனித அதிகாரி எடுப்பார். உங்கள் கோரிக்கைகளைக் காண இடது மெனுவில் 'Reports' என்பதை அழுத்தவும்.",
            "te": f"ఈ వెబ్‌సైట్‌లో మీ {count} క్లెయిమ్‌లు ఉన్నాయి. {crop} పంట కోసం తాజా స్థితి: {status}. గమనిక: తుది నిర్ణయాన్ని మానవ అధికారి తీసుకుంటారు. మీ అన్ని క్లెయిమ్‌లను చూడటానికి ఎడమ సైడ్‌బార్‌లో 'Reports' క్లిక్ చేయండి.",
            "bn": f"এই ওয়েবসাইটে আপনার {count}টি দাবি রয়েছে। {crop} ফসলের সর্বশেষ স্থিতি: {status}। দ্রষ্টব্য: চূড়ান্ত সিদ্ধান্ত মানব কর্মকর্তা নেবেন। আপনার দাবিগুলি দেখতে বাম সাইডবারে 'Reports' ক্লিক করুন।",
            "gu": f"આ વેબસાઇટ પર તમારા {count} દાવો(દાવા) છે. {crop} માટેનો નવીનતમ દાવો સ્થિતિ: {status} છે. નોંધ: અંતિમ નિર્ણય માનવ અધિકારી લે છે. તમારા બધા દાવા જોવા માટે ડાબી બાજુના સાઇડબારમાં 'Reports' પર ક્લિક કરો.",
            "kn": f"ಈ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ನಿಮ್ಮ {count} ಹಕ್ಕುಗಳು ದಾಖಲಾಗಿವೆ. {crop} ಬೆಳೆಗೆ ಇತ್ತೀಚಿನ ಸ್ಥಿತಿ: {status}. ಸೂಚನೆ: ಅಂತಿಮ ನಿರ್ಧಾರವನ್ನು ಮಾನವ ಅಧಿಕಾರಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ. ಎಲ್ಲಾ ಹಕ್ಕುಗಳನ್ನು ನೋಡಲು ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Reports' ಕ್ಲಿಕ್ ಮಾಡಿ.",
            "ml": f"ഈ വെബ്സൈറ്റിൽ നിങ്ങളുടെ {count} ക്ലെയിമുകൾ ഉണ്ട്. {crop} വിളയുടെ പുതിയ നില: {status}. കുറിപ്പ്: അന്തിമ തീരുമാനം മനുഷ്യ ഉദ്യോഗസ്ഥൻ എടുക്കുന്നു. വിവരങ്ങൾ കാണാൻ ഇടത് സൈഡ്ബാറിലെ 'Reports' ക്ലിക്ക് ചെയ്യുക.",
            "pa": f"ਇਸ ਵੈੱਬਸਾਈਟ 'ਤੇ ਤੁਹਾਡੇ {count} ਦਾਅਵੇ ਦਰਜ ਹਨ। {crop} ਫਸਲ ਲਈ ਤਾਜ਼ਾ ਸਥਿਤੀ: {status} ਹੈ। ਨੋਟ: ਅੰਤਿਮ ਫੈਸਲਾ ਮਨੁੱਖੀ ਅਧਿਕਾਰੀ ਕਰਦਾ ਹੈ। ਸਾਰੇ ਦਾਅਵੇ ਦੇਖਣ ਲਈ ਖੱਬੇ ਪਾਸੇ 'Reports' 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "as": f"এই ৱেবছাইটত আপোনাৰ {count}টা দাবী আছে। {crop} শস্যৰ শেহতীয়া স্থিতি: {status}। মন কৰিব: চূড়ান্ত সিদ্ধান্ত মানৱ বিষয়াই লয়। আপোনাৰ সকলো দাবী চাবলৈ বাওঁফালৰ ছাইডবাৰত 'Reports' ক্লিক কৰক।",
            "or": f"ଏହି ୱେବସାଇଟରେ ଆପଣଙ୍କ {count}ଟି ଦାବି ଅଛି। {crop} ଫସଲ ପାଇଁ ସର୍ବଶେଷ ସ୍ଥିତି: {status}। ଧ୍ୟାନ ଦିଅନ୍ତୁ: ଅନ୍ତିମ ନିଷ୍ପତ୍ତି ମାନବ ଅଧିକାରୀ ନିଅନ୍ତି। ଆପଣଙ୍କ ଦାବିଗୁଡ଼ିକ ଦେଖିବାକୁ ବାମ ପାର୍ଶ୍ୱରେ 'Reports' କ୍ଲିକ କରନ୍ତୁ।"
        }
        return summaries.get(language, summaries["en"])
    except Exception:
        return LOGIN_REQUIRED_MESSAGES.get(language, LOGIN_REQUIRED_MESSAGES["en"])

# =========================================================
# COMPREHENSIVE 12-LANGUAGE LOCAL FAST INTENT KNOWLEDGE BASE
# Strictly grounded in THIS project website UI and features.
# =========================================================

LOCAL_RESPONSES = {
    "LOGIN_LOGGED_OUT": {
        "en": "To log in to this website:\n1. Click 'Login / Register' in the left sidebar menu.\n2. Enter your Username and Password.\n3. Click the 'Login' button.\n• If you don't have an account yet, click 'Register' at the bottom of the form to create one.\n• If you forgot your password, click 'Forgot password?' to generate a 32-character reset token.\nOnce logged in, you can access your Dashboard, submit crop damage claims, view satellite NDVI analysis, and track claim reports.",
        "hi": "इस वेबसाइट पर लॉगिन करने के लिए:\n1. बाईं साइडबार मेनू में 'Login / Register' (लॉगिन / पंजीकरण) पर क्लिक करें।\n2. अपना यूज़रनेम (Username) और पासवर्ड (Password) दर्ज करें।\n3. 'Login' बटन पर क्लिक करें।\n• यदि आपका खाता नहीं है, तो नया खाता बनाने के लिए फॉर्म में नीचे दिए गए 'Register' लिंक पर क्लिक करें।\n• यदि आप पासवर्ड भूल गए हैं, तो 'Forgot password?' पर क्लिक करके पासवर्ड रीसेट टोकन प्राप्त करें।\nलॉगिन करने के बाद आप डैशबोर्ड, फसल बीमा दावा, सैटेलाइट विश्लेषण और रिपोर्ट देख सकते हैं।",
        "mr": "या वेबसाइटवर लॉगिन करण्यासाठी:\n1. डाव्या बाजूच्या साइडबारमधील / मेनूमधील 'Login / Register' (लॉगिन / नोंदणी) पर्यायावर क्लिक करा.\n2. तुमचे वापरकर्तानाव (Username) आणि पासवर्ड (Password) प्रविष्ट करा.\n3. 'Login' बटणावर क्लिक करा.\n• नवीन खाते उघडायचे असल्यास खालील 'Register' लिंकवर क्लिक करा.\n• पासवर्ड विसरला असल्यास 'Forgot password?' वर क्लिक करून ३२-अक्षरी पासवर्ड रीसेट टोकन मिळवा.\nलॉगिन केल्यानंतर तुम्ही डॅशबोर्ड, पीक नुकसान दावा सादर करणे, उपग्रह NDVI विश्लेषण आणि अहवाल पाहू शकता.",
        "ta": "இந்த இணையதளத்தில் லாகின் செய்ய:\n1. இடது பக்க மெனுவில் 'Login / Register' என்பதைத் திறக்கவும்.\n2. உங்கள் பயனர்பெயர் (Username) மற்றும் கடவுச்சொல்லை (Password) உள்ளிடவும்.\n3. 'Login' பொத்தானை அழுத்தவும்.\n• கணக்கு இல்லையென்றால் 'Register' என்பதை அழுத்தி புதிய கணக்கை உருவாக்கவும்.\n• கடவுச்சொல்லை மறந்திருந்தால் 'Forgot password?' மூலம் ரீசெட் டோக்கன் பெறலாம்.",
        "te": "ఈ వెబ్‌సైట్‌లో లాగిన్ చేయడానికి:\n1. ఎడమ వైపు మెనూలో 'Login / Register' క్లిక్ చేయండి.\n2. మీ యూజర్‌నేమ్ (Username) మరియు పాస్‌వర్డ్ (Password) నమోదు చేయండి.\n3. 'Login' బటన్ పై క్లిక్ చేయండి.\n• ఖాతా లేకపోతే 'Register' పై క్లిక్ చేసి కొత్త ఖాతా సృష్టించండి.\n• పాస్‌వర్డ్ మర్చిపోతే 'Forgot password?' ద్వారా రీసెట్ టోకెన్ పొందవచ్చు.",
        "bn": "এই ওয়েবসাইটে লগইন করতে:\n১. বাম সাইডবারে 'Login / Register' এ ক্লিক করুন।\n২. আপনার ব্যবহারকারীর নাম (Username) ও পাসওয়ার্ড (Password) লিখুন।\n৩. 'Login' বাটনে চাপুন।\n• একাউন্ট না থাকলে 'Register' এ ক্লিক করে নতুন একাউন্ট তৈরি করুন।\n• পাসওয়ার্ড ভুলে গেলে 'Forgot password?' এর মাধ্যমে রিসেট টোকেন পান।",
        "gu": "આ વેબસાઇટ પર લૉગિન કરવા માટે:\n1. ડાબી બાજુના સાઇડબારમાં 'Login / Register' પર ક્લિક કરો.\n2. તમારું વપરાશકર્તાનામ (Username) અને પાસવર્ડ (Password) દાખલ કરો.\n3. 'Login' બટન પસંદ કરો.\n• ખાતું ન હોય તો 'Register' પર ક્લિક કરીને નવું ખાતું બનાવો.\n• પાસવર્ડ ભૂલી ગયા હોવ તો 'Forgot password?' થી રીસેટ ટોકન મેળવો.",
        "kn": "ಈ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಲಾಗಿನ್ ಮಾಡಲು:\n1. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Login / Register' ಕ್ಲಿಕ್ ಮಾಡಿ.\n2. ನಿಮ್ಮ ಬಳಕೆದಾರ ಹೆಸರು (Username) ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ (Password) ನಮೂದಿಸಿ.\n3. 'Login' ಬಟನ್ ಒತ್ತಿ.\n• ಖಾತೆ ಇಲ್ಲದಿದ್ದರೆ ಹೊಸ ಖಾತೆ ರಚಿಸಲು 'Register' ಕ್ಲಿಕ್ ಮಾಡಿ.\n• ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿದ್ದರೆ 'Forgot password?' ಮೂಲಕ ರಿಸೆಟ್ ಟೋಕನ್ ಪಡೆಯಿರಿ.",
        "ml": "ഈ വെബ്സൈറ്റിൽ ലോഗിൻ ചെയ്യാൻ:\n1. ഇടത് സൈഡ്ബാറിലെ 'Login / Register' ക്ലിക്ക് ചെയ്യുക.\n2. നിങ്ങളുടെ ഉപയോക്തൃനാമവും (Username) പാസ്‌വേഡും (Password) നൽകുക.\n3. 'Login' ബട്ടൺ അമർത്തുക.\n• അക്കൗണ്ട് ഇല്ലെങ്കിൽ 'Register' ക്ലിക്ക് ചെയ്ത് പുതിയത് ഉണ്ടാക്കുക.\n• പാസ്‌വേഡ് മറന്നുപോയെങ്കിൽ 'Forgot password?' വഴി റീസെറ്റ് ടോക്കൺ എടുക്കുക.",
        "pa": "ਇਸ ਵੈੱਬਸਾਈਟ 'ਤੇ ਲੌਗਇਨ ਕਰਨ ਲਈ:\n1. ਖੱਬੇ ਪਾਸੇ 'Login / Register' 'ਤੇ ਕਲਿੱਕ ਕਰੋ।\n2. ਆਪਣਾ ਯੂਜ਼ਰਨੇਮ (Username) ਅਤੇ ਪਾਸਵਰਡ (Password) ਦਰਜ ਕਰੋ।\n3. 'Login' ਬਟਨ ਦਬਾਓ।\n• ਜੇਕਰ ਖਾਤਾ ਨਹੀਂ ਹੈ ਤਾਂ 'Register' 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਨਵਾਂ ਖਾਤਾ ਬਣਾਓ।\n• ਪਾਸਵਰਡ ਭੁੱਲਣ 'ਤੇ 'Forgot password?' ਰਾਹੀਂ ਰੀਸੈਟ ਟੋਕਨ ਪ੍ਰਾਪਤ ਕਰੋ।",
        "as": "এই ৱেবছাইটত লগইন কৰিবলৈ:\n১. বাওঁফালৰ ছাইডবাৰত 'Login / Register' ক্লিক কৰক।\n২. আপোনাৰ ইউজাৰনেম (Username) আৰু পাছৱৰ্ড (Password) দিয়ক।\n৩. 'Login' বুটামত ক্লিক কৰক।\n• নতুন একাউণ্টৰ বাবে 'Register' ত ক্লিক কৰক।\n• পাছৱৰ্ড পাহৰিলে 'Forgot password?' ব্যৱহাৰ কৰক।",
        "or": "ଏହି ୱେବସାଇଟରେ ଲଗଇନ କରିବାକୁ:\n୧. ବାମ ପାର୍ଶ୍ୱରେ ଥିବା 'Login / Register' କ୍ଲିକ କରନ୍ତୁ।\n୨. ଆପଣଙ୍କ ୟୁଜରନେମ (Username) ଏବଂ ପାସୱାର୍ଡ (Password) ଦିଅନ୍ତୁ।\n୩. 'Login' ବଟନ ଦବାନ୍ତୁ।\n• ଖାତା ନଥିଲେ 'Register' କ୍ଲିକ କରି ନୂଆ ଖାତା ଖୋଲନ୍ତୁ।\n• ପାସୱାର୍ଡ ଭୁଲିଯାଇଥିଲେ 'Forgot password?' ବ୍ୟବହାର କରନ୍ତୁ।"
    },

    "LOGIN_LOGGED_IN": {
        "en": "You are already logged in as {name} ({username}) from {district}, {state}.\n\nYou have full access to all features from the left sidebar:\n• 📊 Dashboard — Satellite vegetation & study area overview\n• 🗺️ Damage Analysis & 📍 Study Area — Sentinel-2 NDVI inspection\n• 🛡️ Insurance Claim — Submit crop damage loss and upload photo\n• 📄 Reports — View your submitted claims and AI review status\n• 📊 AI/ML Performance — View MobileNetV2 evaluation metrics\n\nIf you want to log into another account, click the Logout button (⎋) in your profile card at the bottom of the sidebar.",
        "hi": "आप वर्तमान में {district}, {state} से {name} ({username}) के रूप में पहले से लॉगिन हैं।\n\nआप बाईं साइडबार से सभी सुविधाओं का उपयोग कर सकते हैं:\n• 📊 Dashboard — उपग्रह वनस्पति सूचकांक और अध्ययन क्षेत्र सारांश\n• 🗺️ Damage Analysis व 📍 Study Area — सेंटिनल-2 उपग्रह NDVI जांच\n• 🛡️ Insurance Claim — फसल क्षति विवरण और फोटो सबमिट करें\n• 📄 Reports — अपने पिछले दावों की स्थिति और AI परिणाम देखें\n• 📊 AI/ML Performance — मॉडल मूल्यांकन और मेट्रिक्स देखें\n\nयदि आप किसी अन्य खाते में लॉगिन करना चाहते हैं, तो साइडबार में नीचे प्रोफाइल कार्ड में लॉगआउट (⎋) बटन पर क्लिक करें।",
        "mr": "तुम्ही आधीच {district}, {state} येथून {name} ({username}) म्हणून या वेबसाइटवर लॉग इन आहात.\n\nतुम्ही डाव्या बाजूच्या साइडबार मेनूमधून सर्व सुविधा वापरू शकता:\n• 📊 Dashboard — उपग्रह पीक आरोग्य आणि अभ्यास क्षेत्र आढावा\n• 🗺️ Damage Analysis व 📍 Study Area — Sentinel-2 NDVI तपासणी\n• 🛡️ Insurance Claim — पिकाचे नुकसान आणि फोटो सादर करा\n• 📄 Reports — तुमचे सादर केलेले दावे आणि AI समीक्षा स्थिती तपासा\n• 📊 AI/ML Performance — मॉडेल मूल्यांकन मेट्रिक्स पहा\n\nदुसऱ्या खात्यात लॉगिन करायचे असल्यास डाव्या साइडबारच्या तळाशी प्रोफाइल कार्डमधील लॉगआउट (⎋) बटण दाबा.",
        "ta": "நீங்கள் ஏற்கனவே {name} ({username}), {district}, {state} என உள்நுழைந்துள்ளீர்கள்.\nஇடது மெனு மூலம் Dashboard, Insurance Claim, Reports மற்றும் AI/ML Performance ஆகியவற்றை அணுகலாம். வெளியேற கீழே உள்ள Logout (⎋) பொத்தானை அழுத்தவும்.",
        "te": "మీరు ఇప్పటికే {name} ({username}), {district}, {state} గా లాగిన్ అయి ఉన్నారు.\nఎడమ సైడ్‌బార్ ద్వారా Dashboard, Insurance Claim, Reports మరియు AI/ML Performance ఫీచర్లను ఉపయోగించవచ్చు. లాగౌట్ కావడానికి కింద ఉన్న Logout (⎋) బటన్ నొక్కండి.",
        "bn": "আপনি ইতিমধ্যেই {name} ({username}), {district}, {state} হিসেবে লগইন আছেন।\nবাম সাইডবার থেকে Dashboard, Insurance Claim, Reports ও AI/ML Performance ব্যবহার করতে পারেন। লগআউট করতে নিচে Logout (⎋) বাটনে ক্লিক করুন।",
        "gu": "તમે પહેલાથી જ {name} ({username}), {district}, {state} તરીકે લૉગિન છો.\nડાબી બાજુના સાઇડબારથી Dashboard, Insurance Claim, Reports અને AI/ML Performance ઍક્સેસ કરી શકો છો. લૉગઆઉટ કરવા નીચે Logout (⎋) ક્લિક કરો.",
        "kn": "ನೀವು ಈಗಾಗಲೇ {name} ({username}), {district}, {state} ಆಗಿ ಲಾಗಿನ್ ಆಗಿದ್ದೀರಿ.\nಎಡ ಸೈಡ್‌ಬಾರ್‌ನಿಂದ Dashboard, Insurance Claim, Reports ಮತ್ತು AI/ML Performance ಬಳಸಬಹುದು. ಲಾಗ್‌ಔಟ್ ಮಾಡಲು ಕೆಳಗಿನ Logout (⎋) ಒತ್ತಿ.",
        "ml": "നിങ്ങൾ ഇപ്പോൾ {name} ({username}), {district}, {state} ആയി ലോഗിൻ ചെയ്തിട്ടുണ്ട്.\nഇടത് സൈഡ്ബാറിലൂടെ Dashboard, Insurance Claim, Reports എന്നിവ ഉപയോഗിക്കാം. ലോഗൗട്ട് ചെയ്യാൻ താഴെയുള്ള Logout (⎋) അമർത്തുക.",
        "pa": "ਤੁਸੀਂ ਪਹਿਲਾਂ ਹੀ {name} ({username}), {district}, {state} ਵਜੋਂ ਲੌਗਇਨ ਹੋ।\nਖੱਬੇ ਪਾਸੇ ਤੋਂ Dashboard, Insurance Claim, Reports ਅਤੇ AI/ML Performance ਵਰਤ ਸਕਦੇ ਹੋ। ਲੌਗਆਉਟ ਕਰਨ ਲਈ ਹੇਠਾਂ Logout (⎋) ਬਟਨ ਦਬਾਓ।",
        "as": "আপুনি ইতিমধ্যে {name} ({username}), {district}, {state} হিচাপে লগইন হৈ আছে।\nবাওঁফালৰ পৰা Dashboard, Insurance Claim, Reports ব্যৱহাৰ কৰিব পাৰে। লগআউট কৰিবলৈ তলৰ Logout (⎋) বুটাম টিপক।",
        "or": "ଆପଣ ପୂର୍ବରୁ {name} ({username}), {district}, {state} ଭାବେ ଲଗଇନ ଅଛନ୍ତି।\nବାମ ପାର୍ଶ୍ୱରୁ Dashboard, Insurance Claim, Reports ଏବଂ AI/ML Performance ବ୍ୟବହାର କରିପାରିବେ। ଲଗଆଉଟ୍ ପାଇଁ ତଳେ ଥିବା Logout (⎋) କ୍ଲିକ କରନ୍ତୁ।"
    },

    "REGISTER": {
        "en": "To register a new farmer account on this website:\n1. Click 'Login / Register' in the left sidebar.\n2. Switch to the 'Register' tab.\n3. Fill in your details:\n   • Full Name\n   • Phone Number (10 digits)\n   • Email Address\n   • State and District (selected from dropdown)\n   • Desired Username\n   • Password and Confirm Password\n4. Click the 'Register' button.\nYour account is created immediately and you will be logged into your new farmer session.",
        "hi": "इस वेबसाइट पर नया खाता बनाने (पंजीकरण) के लिए:\n1. बाईं साइडबार में 'Login / Register' पर क्लिक करें।\n2. 'Register' (पंजीकरण) टैब चुनें।\n3. अपनी जानकारी भरें:\n   • पूरा नाम (Full Name)\n   • मोबाइल नंबर (10 अंक)\n   • ईमेल आईडी (Email)\n   • राज्य (State) और जिला (District) ड्रॉपडाउन से चुनें\n   • यूज़रनेम (Username)\n   • पासवर्ड और पासवर्ड की पुष्टि (Confirm Password)\n4. 'Register' बटन दबाएं। आपका खाता तुरंत सक्रिय हो जाएगा।",
        "mr": "या वेबसाइटवर नवीन शेतकरी खाते नोंदणी करण्यासाठी:\n1. डाव्या बाजूच्या साइडबारमधील 'Login / Register' वर क्लिक करा.\n2. 'Register' (नोंदणी) टॅब निवडा.\n3. पुढील माहिती भरा:\n   • पूर्ण नाव (Full Name)\n   • मोबाईल क्रमांक (10 अंक)\n   • ईमेल आयडी (Email)\n   • राज्य आणि जिल्हा (ड्रॉपडाउनमधून निवडा)\n   • वापरकर्तानाव (Username)\n   • पासवर्ड आणि पासवर्डची खात्री (Confirm Password)\n4. 'Register' बटणावर क्लिक करा. तुमचे खाते लगेच तयार होईल.",
        "ta": "புதிய கணக்கு பதிவு செய்ய:\n1. இடது மெனுவில் 'Login / Register' திறந்து 'Register' தாவலைத் தேர்ந்தெடுக்கவும்.\n2. பெயர், தொலைபேசி எண், மின்னஞ்சல், மாநிலம், மாவட்டம், பயனர்பெயர் மற்றும் கடவுச்சொல் உள்ளிடவும்.\n3. 'Register' பொத்தானை அழுத்தவும். கணக்கு உடனடியாக உருவாக்கப்படும்.",
        "te": "కొత్త ఖాతా రిజిస్టర్ చేయడానికి:\n1. ఎడమ సైడ్‌బార్‌లో 'Login / Register' తెరిచి 'Register' ట్యాబ్ ఎంచుకోండి.\n2. పేరు, ఫోన్ నంబర్, ఈమెయిల్, రాష్ట్రం, జిల్లా, యూజర్‌నేమ్ మరియు పాస్‌వర్డ్ నమోదు చేయండి.\n3. 'Register' బటన్ క్లిక్ చేయండి. ఖాతా వెంటనే ప్రారంభమవుతుంది.",
        "bn": "নতুন একাউন্ট নিবন্ধন করতে:\n১. বাম সাইডবারে 'Login / Register' খুলে 'Register' ট্যাব নির্বাচন করুন।\n২. নাম, ফোন নম্বর, ইমেইল, রাজ্য, জেলা, ব্যবহারকারীর নাম ও পাসওয়ার্ড দিন।\n৩. 'Register' বাটনে চাপুন। একাউন্টটি সাথে সাথে তৈরি হয়ে যাবে।",
        "gu": "નવું ખાતું બનાવવા માટે:\n1. ડાબી બાજુના સાઇડબારમાં 'Login / Register' ખોલીને 'Register' ટેબ પસંદ કરો.\n2. નામ, ફોન નંબર, ઇમેઇલ, રાજ્ય, જિલ્લો, વપરાશકર્તાનામ અને પાસવર્ડ ભરો.\n3. 'Register' બટન દબાવો. ખાતું તરત જ બની જશે.",
        "kn": "ಹೊಸ ಖಾತೆ ನೋಂದಾಯಿಸಲು:\n1. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Login / Register' ತೆರೆದು 'Register' ಟ್ಯಾಬ್ ಆಯ್ಕೆಮಾಡಿ.\n2. ಹೆಸರು, ಮೊಬೈಲ್, ಇಮೇಲ್, ರಾಜ್ಯ, ಜಿಲ್ಲೆ, ಬಳಕೆದಾರ ಹೆಸರು ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ಭರ್ತಿ ಮಾಡಿ.\n3. 'Register' ಒತ್ತಿ. ಖಾತೆ ತಕ್ಷಣ ಸಕ್ರಿಯಗೊಳ್ಳುತ್ತದೆ.",
        "ml": "പുതിയ അക്കൗണ്ട് രജിസ്റ്റർ ചെയ്യാൻ:\n1. ഇടത് സൈഡ്ബാറിലെ 'Login / Register' തുറന്ന് 'Register' ടാബ് തിരഞ്ഞെടുക്കുക.\n2. പേര്, ഫോൺ, ഇമെയിൽ, സംസ്ഥാനം, ജില്ല, യൂസർനെയിം, പാസ്‌വേഡ് എന്നിവ നൽകുക.\n3. 'Register' ബട്ടൺ അമർത്തുക.",
        "pa": "ਨਵਾਂ ਖਾਤਾ ਬਣਾਉਣ ਲਈ:\n1. ਖੱਬੇ ਪਾਸੇ 'Login / Register' ਖੋਲ੍ਹ ਕੇ 'Register' ਟੈਬ ਚੁਣੋ।\n2. ਆਪਣਾ ਨਾਮ, ਫ਼ੋਨ, ਈਮੇਲ, ਰਾਜ, ਜ਼ਿਲ੍ਹਾ, ਯੂਜ਼ਰਨੇਮ ਅਤੇ ਪਾਸਵਰਡ ਭਰੋ।\n3. 'Register' ਬਟਨ ਦਬਾਓ। ਖਾਤਾ ਤੁਰੰਤ ਬਣ ਜਾਵੇਗਾ।",
        "as": "নতুন একাউণ্ট পঞ্জীয়ন কৰিবলৈ:\n১. বাওঁফালৰ 'Login / Register' খোলক আৰু 'Register' বাছক।\n২. নাম, ফোন, ইমেইল, ৰাজ্য, জিলা, ইউজাৰনেম আৰু পাছৱৰ্ড দিয়ক।\n৩. 'Register' ক্লিক কৰক। একাউণ্ট তৎক্ষণাত সক্ৰিয় হ'ব।",
        "or": "ନୂଆ ଖାତା ପଞ୍ଜୀକରଣ ପାଇଁ:\n୧. ବାମ ପାର୍ଶ୍ୱରେ 'Login / Register' ଖୋଲି 'Register' ଟ୍ୟାବ ବାଛନ୍ତୁ।\n୨. ନାମ, ଫୋନ, ଇମେଲ, ରାଜ୍ୟ, ଜିଲ୍ଲା, ୟୁଜରନେମ ଓ ପାସୱାର୍ଡ ଦିଅନ୍ତୁ।\n୩. 'Register' କ୍ଲିକ କରନ୍ତୁ। ଖାତା ତୁରନ୍ତ ତିଆରି ହୋଇଯିବ।"
    },

    "FORGOT_PASSWORD": {
        "en": "To reset your password on this website:\n1. Open 'Login / Register' in the left sidebar.\n2. Click 'Forgot password?' below the login button.\n3. Enter your Username or Email address and click 'Send Reset Token'. The system will generate a 32-character reset token.\n4. Click 'Already have a reset token?' to switch to the Reset Password view.\n5. Enter your reset token, your new password, and confirm password, then click 'Reset Password'.\nYou can then log in with your new password.",
        "hi": "इस वेबसाइट पर अपना पासवर्ड रीसेट करने के लिए:\n1. बाईं साइडबार में 'Login / Register' खोलें।\n2. लॉगिन बटन के नीचे 'Forgot password?' (पासवर्ड भूल गए?) पर क्लिक करें।\n3. अपना यूज़रनेम या ईमेल आईडी दर्ज करें और 'Send Reset Token' पर क्लिक करें। सिस्टम आपको 32 अक्षरों का रीसेट टोकन प्रदान करेगा।\n4. 'Already have a reset token?' पर क्लिक करें।\n5. अपना रीसेट टोकन, नया पासवर्ड और पासवर्ड पुष्टि दर्ज करें और 'Reset Password' दबाएं।\nइसके बाद आप नए पासवर्ड से लॉगिन कर सकते हैं।",
        "mr": "या वेबसाइटवर तुमचा पासवर्ड रीसेट करण्यासाठी:\n1. डाव्या बाजूच्या साइडबार मेनूमधील 'Login / Register' उघडा.\n2. खाली दिलेल्या 'Forgot password?' पर्यायावर क्लिक करा.\n3. तुमचे वापरकर्तानाव किंवा ईमेल भरा आणि 'Send Reset Token' वर क्लिक करा. सिस्टम तुम्हाला ३२ अक्षरी रीसेट टोकन देईल.\n4. 'Already have a reset token?' वर क्लिक करा.\n5. मिळालेला टोकन, नवीन पासवर्ड आणि पासवर्ड खात्री प्रविष्ट करा व 'Reset Password' दाबा.\nत्यानंतर तुम्ही नवीन पासवर्डने लगेच लॉगिन करू शकता.",
        "ta": "கடவுச்சொல்லை மீட்டமைக்க:\n1. 'Login / Register' திறந்து 'Forgot password?' என்பதை அழுத்தவும்.\n2. பயனர்பெயர் அல்லது மின்னஞ்சல் உள்ளிட்டு 'Send Reset Token' என்பதை அழுத்தவும். 32-எழுத்து டோக்கன் கிடைக்கும்.\n3. 'Already have a reset token?' அழுத்தி, டோக்கன் மற்றும் புதிய கடவுச்சொல்லை உள்ளிட்டு 'Reset Password' அழுத்தவும்.",
        "te": "పాస్‌వర్డ్ రీసెట్ చేయడానికి:\n1. 'Login / Register' తెరిచి 'Forgot password?' క్లిక్ చేయండి.\n2. యూజర్‌నేమ్ లేదా ఈమెయిల్ ఇచ్చి 'Send Reset Token' క్లిక్ చేయండి. 32-అక్షరాల టోకెన్ వస్తుంది.\n3. 'Already have a reset token?' ఎంచుకుని, టోకెన్ మరియు కొత్త పాస్‌వర్డ్ నమోదు చేసి 'Reset Password' నొక్కండి.",
        "bn": "পাসওয়ার্ড রিসেট করতে:\n১. 'Login / Register' খুলে 'Forgot password?' এ ক্লিক করুন।\n২. ব্যবহারকারীর নাম বা ইমেইল দিয়ে 'Send Reset Token' চাপুন। ৩২ অক্ষরের টোকেন তৈরি হবে।\n৩. 'Already have a reset token?' এ গিয়ে টোকেন ও নতুন পাসওয়ার্ড দিয়ে 'Reset Password' চাপুন।",
        "gu": "પાસવર્ડ રીસેટ કરવા માટે:\n1. 'Login / Register' માં જઈને 'Forgot password?' પર ક્લિક કરો.\n2. વપરાશકર્તાનામ કે ઇમેઇલ આપીને 'Send Reset Token' દબાવો. 32 અક્ષરનો ટોકન મળશે.\n3. 'Already have a reset token?' પર જઈને ટોકન અને નવો પાસવર્ડ દાખલ કરી 'Reset Password' કરો.",
        "kn": "ಪಾಸ್‌ವರ್ಡ್ ರಿಸೆಟ್ ಮಾಡಲು:\n1. 'Login / Register' ನಲ್ಲಿ 'Forgot password?' ಕ್ಲಿಕ್ ಮಾಡಿ.\n2. ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಇಮೇಲ್ ನಮೂದಿಸಿ 'Send Reset Token' ಒತ್ತಿ. 32 ಅಕ್ಷರಗಳ ಟೋಕನ್ ದೊರೆಯುತ್ತದೆ.\n3. 'Already have a reset token?' ಆಯ್ಕೆಮಾಡಿ ಟೋಕನ್ ಮತ್ತು ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ನೀಡಿ 'Reset Password' ಮಾಡಿ.",
        "ml": "പാസ്‌വേഡ് റീസെറ്റ് ചെയ്യാൻ:\n1. 'Login / Register' തുറന്ന് 'Forgot password?' ക്ലിക്ക് ചെയ്യുക.\n2. യൂസർനെയിം അല്ലെങ്കിൽ ഇമെയിൽ നൽകി 'Send Reset Token' അമർത്തുക.\n3. ലഭിച്ച 32-അക്ഷര ടോക്കണും പുതിയ പാസ്‌വേഡും നൽകി 'Reset Password' ചെയ്യുക.",
        "pa": "ਪਾਸਵਰਡ ਰੀਸੈਟ ਕਰਨ ਲਈ:\n1. 'Login / Register' ਵਿੱਚ ਜਾ ਕੇ 'Forgot password?' 'ਤੇ ਕਲਿੱਕ ਕਰੋ।\n2. ਯੂਜ਼ਰਨੇਮ ਜਾਂ ਈਮੇਲ ਦਰਜ ਕਰਕੇ 'Send Reset Token' ਦਬਾਓ। 32 ਅੱਖਰਾਂ ਦਾ ਟੋਕਨ ਮਿਲੇਗਾ।\n3. 'Already have a reset token?' ਚੁਣ ਕੇ ਟੋਕਨ ਅਤੇ ਨਵਾਂ ਪਾਸਵਰਡ ਭਰੋ ਅਤੇ 'Reset Password' ਕਰੋ।",
        "as": "পাছৱৰ্ড ৰিচেট কৰিবলৈ:\n১. 'Login / Register' ত 'Forgot password?' ক্লিক কৰক।\n২. ইউজাৰনেম বা ইমেইল দি 'Send Reset Token' টিপক।\n৩. 'Already have a reset token?' ত গৈ টোকেন আৰু নতুন পাছৱৰ্ড দি 'Reset Password' কৰক।",
        "or": "ପାସୱାର୍ଡ ରିସେଟ୍ କରିବାକୁ:\n୧. 'Login / Register' ରେ 'Forgot password?' କ୍ଲିକ କରନ୍ତୁ।\n୨. ୟୁଜରନେମ ବା ଇମେଲ ଦେଇ 'Send Reset Token' ଦବାନ୍ତୁ। ୩୨ ଅକ୍ଷରର ଟୋକନ ମିଳିବ।\n୩. 'Already have a reset token?' ରେ ଟୋକନ ଏବଂ ନୂଆ ପାସୱାର୍ଡ ଦେଇ 'Reset Password' କରନ୍ତୁ।"
    },

    "SUBMIT_CLAIM": {
        "en": "To submit an insurance claim on this website:\n1. Click 'Insurance Claim' in the left sidebar menu (make sure you are logged in).\n2. Fill in the claim details:\n   • Crop Name (e.g. Wheat, Soybean, Cotton, Rice)\n   • Claimed Loss % (between 0 and 100)\n   • Farm Area (in hectares)\n   • Farm Location (village / tehsil)\n   • Event Type (Flood, Drought, Cyclone, Pest/Disease, Hail/Unseasonal Rain, Other)\n   • Crop Stage (Vegetative, Flowering, Maturity, Harvested)\n   • Sowing Date and Claim Date\n3. Upload a clear photograph of your damaged crop.\n4. Click 'Submit Claim'.\nThe system will instantly run MobileNetV2 disease diagnosis, heuristic damage estimation, weather verification checks, and assign an AI review triage band (Normal, Medium, High Review).",
        "hi": "इस वेबसाइट पर फसल बीमा दावा जमा करने के लिए:\n1. बाईं साइडबार में 'Insurance Claim' (बीमा दावा) पर क्लिक करें (सुनिश्चित करें कि आप लॉगिन हैं)।\n2. दावा विवरण भरें:\n   • फसल का नाम (जैसे गेहूँ, सोयाबीन, कपास, धान)\n   • दावा किया गया नुकसान % (0 से 100)\n   • खेत का क्षेत्रफल (हेक्टेयर में)\n   • खेत का स्थान (गाँव / तहसील)\n   • आपदा का प्रकार (बाढ़, सूखा, चक्रवात, कीट/रोग, बेमौसम बारिश, अन्य)\n   • फसल अवस्था (वानस्पतिक, फूल आना, परिपक्वता, कटाई)\n   • बुवाई की तारीख और दावा तारीख\n3. क्षतिग्रस्त फसल की स्पष्ट फोटो अपलोड करें।\n4. 'Submit Claim' पर क्लिक करें।\nप्रणाली तुरंत MobileNetV2 रोग पहचान, दृश्य क्षति अनुमान, मौसम सत्यापन करेगी और समीक्षा श्रेणी (Normal, Medium, High) निर्धारित करेगी।",
        "mr": "या वेबसाइटवर पीक विमा दावा सादर करण्यासाठी:\n1. डाव्या बाजूच्या साइडबार मेनूमधील 'Insurance Claim' (विमा दावा) पर्यायावर क्लिक करा (तुम्ही लॉगिन असणे आवश्यक आहे).\n2. दाव्याचा तपशील भरा:\n   • पिकाचे नाव (उदा. गहू, सोयाबीन, कापूस, भात)\n   • दावा केलेले नुकसान % (० ते १००)\n   • शेताचे क्षेत्रफळ (हेक्टरमध्ये)\n   • शेताचे ठिकाण (गाव / तालुका)\n   • आपत्ती प्रकार (पूर, दुष्काळ, कीड/रोग, चक्रीवादळ, अवकाळी पाऊस, इतर)\n   • पीक अवस्था (वाढ, फुलोरा, पक्वता, काढणी)\n   • पेरणी तारीख आणि दावा तारीख\n3. नुकसान झालेल्या पिकाचा स्पष्ट फोटो अपलोड करा.\n4. 'Submit Claim' बटणावर क्लिक करा.\nप्रणाली त्वरित MobileNetV2 रोग निदान, दृश्यमान नुकसान अंदाज, हवामान पडताळणी करेल आणि पुनरावलोकन श्रेणी (Normal, Medium, High) ठरवेल.",
        "ta": "காப்பீட்டு கோரிக்கையை சமர்ப்பிக்க:\n1. இடது மெனுவில் 'Insurance Claim' என்பதைத் திறக்கவும் (உள்நுழைந்திருக்க வேண்டும்).\n2. பயிர் பெயர், இழப்பு %, பண்ணை பரப்பளவு (ஹெக்டேர்), இடம், பேரிடர் வகை மற்றும் தேதிகளை உள்ளிடவும்.\n3. சேதமடைந்த பயிர் புகைப்படத்தை பதிவேற்றவும்.\n4. 'Submit Claim' என்பதை அழுத்தவும். AI நோய் கணிப்பு மற்றும் ஆய்வு நிலை உடனடியாக உருவாக்கப்படும்.",
        "te": "బీమా క్లెయిమ్ సమర్పించడానికి:\n1. ఎడమ సైడ్‌బార్‌లో 'Insurance Claim' తెరిచి (లాగిన్ అయి ఉండాలి).\n2. పంట పేరు, నష్టం %, విస్తీర్ణం (హెక్టార్లు), స్థానం, విపత్తు రకం మరియు తేదీలు నమోదు చేయండి.\n3. దెబ్బతిన్న పంట ఫోటోను అప్‌లోడ్ చేయండి.\n4. 'Submit Claim' క్లిక్ చేయండి. AI రోగ నిర్ధారణ మరియు సమీక్ష ప్రాధాన్యత వెంటనే నిర్ణయించబడతాయి.",
        "bn": "বিমা দাবি জমা দিতে:\n১. বাম সাইডবারে 'Insurance Claim' খুলুন (লগইন করা আবশ্যক)।\n২. ফসলের নাম, ক্ষতির %, জমির আয়তন (হেক্টর), স্থান, দুর্যোগের ধরন ও তারিখ পূরণ করুন।\n৩. ক্ষতিগ্রস্ত ফসলের স্পষ্ট ছবি আপলোড করুন।\n৪. 'Submit Claim' বাটনে চাপুন। AI রোগ নির্ণয় ও পর্যালোচনা ব্যান্ড স্বয়ংক্রিয়ভাবে তৈরি হবে।",
        "gu": "વીમા દાવો સબમિટ કરવા માટે:\n1. ડાબી બાજુના સાઇડબારમાં 'Insurance Claim' ખોલો (લૉગિન હોવું જરૂરી છે).\n2. પાકનું નામ, નુકસાન %, વિસ્તાર (હેક્ટર), સ્થળ, આપત્તિનો પ્રકાર અને તારીખો ભરો.\n3. ક્ષતિગ્રસ્ત પાકનો સ્પષ્ટ ફોટો અપલોડ કરો.\n4. 'Submit Claim' ક્લિક કરો. સિસ્ટમ AI રોગ અને સમીક્ષા સ્થિતિ તરત નક્કી કરશે.",
        "kn": "ವಿಮಾ ಹಕ್ಕು ಸಲ್ಲಿಸಲು:\n1. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Insurance Claim' ತೆರೆಯಿರಿ (ಲಾಗಿನ್ ಆಗಿರಬೇಕು).\n2. ಬೆಳೆ ಹೆಸರು, ನಷ್ಟ %, ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಹೆಕ್ಟೇರ್), ಸ್ಥಳ, ವಿಪತ್ತಿನ ಪ್ರಕಾರ ಮತ್ತು ದಿನಾಂಕಗಳನ್ನು ನಮೂದಿಸಿ.\n3. ಹಾನಿಯಾದ ಬೆಳೆಯ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.\n4. 'Submit Claim' ಒತ್ತಿ. AI ರೋಗ ನಿರ್ಣಯ ಮತ್ತು ಪರಿಶೀಲನಾ ಹಂತ ತಕ್ಷಣ ನಿರ್ಧಾರವಾಗುತ್ತದೆ.",
        "ml": "ഇൻഷുറൻസ് ക്ലെയിം സമർപ്പിക്കാൻ:\n1. ഇടത് സൈഡ്ബാറിലെ 'Insurance Claim' തുറക്കുക (ലോഗിൻ ചെയ്തിരിക്കണം).\n2. വിള, നഷ്ടം %, വിസ്തീർണ്ണം, സ്ഥലം, ദുരന്ത തരം, തീയതികൾ എന്നിവ നൽകുക.\n3. വിളനാശ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക.\n4. 'Submit Claim' അമർത്തുക. AI വിശകലനം ഉടൻ ലഭിക്കും.",
        "pa": "ਬੀਮਾ ਦਾਅਵਾ ਪੇਸ਼ ਕਰਨ ਲਈ:\n1. ਖੱਬੇ ਪਾਸੇ 'Insurance Claim' ਖੋਲ੍ਹੋ (ਲੌਗਇਨ ਹੋਣਾ ਜ਼ਰੂਰੀ ਹੈ)।\n2. ਫਸਲ ਦਾ ਨਾਮ, ਨੁਕਸਾਨ %, ਰਕਬਾ (ਹੈਕਟੇਅਰ), ਸਥਾਨ, ਆਫ਼ਤ ਦੀ ਕਿਸਮ ਅਤੇ ਤਾਰੀਖਾਂ ਭਰੋ।\n3. ਖਰਾਬ ਫਸਲ ਦੀ ਫੋਟੋ ਅੱਪਲੋਡ ਕਰੋ।\n4. 'Submit Claim' ਦਬਾਓ। AI ਵਿਸ਼ਲੇਸ਼ਣ ਅਤੇ ਸਮੀਖਿਆ ਦਰਜਾ ਤੁਰੰਤ ਮਿਲੇਗਾ।",
        "as": "বীমা দাবী দাখিল কৰিবলৈ:\n১. বাওঁফালৰ 'Insurance Claim' খোলক (লগইন থকাটো প্ৰয়োজন)।\n২. শস্যৰ নাম, ক্ষতিৰ %, কালি (হেক্টৰ), স্থান, দুৰ্যোগৰ প্ৰকাৰ আৰু তাৰিখ দিয়ক।\n৩. ক্ষতিগ্ৰস্ত শস্যৰ ফটো আপল'ড কৰক।\n৪. 'Submit Claim' ক্লিক কৰক। AI বিশ্লেষণ তৎক্ষণাত সম্পন্ন হ'ব।",
        "or": "ବୀମା ଦାବି ଦାଖଲ କରିବାକୁ:\n୧. ବାମ ପାର୍ଶ୍ୱରେ 'Insurance Claim' ଖୋଲନ୍ତୁ (ଲଗଇନ ରହିବା ଆବଶ୍ୟକ)।\n୨. ଫସଲ ନାମ, କ୍ଷତି %, ଜମି ଆୟତନ (ହେକ୍ଟର), ସ୍ଥାନ, ବିପର୍ଯ୍ୟୟ ପ୍ରକାର ଓ ତାରିଖ ପୂରଣ କରନ୍ତୁ।\n୩. କ୍ଷତିଗ୍ରସ୍ତ ଫସଲର ଫଟୋ ଅପଲୋଡ କରନ୍ତୁ।\n୪. 'Submit Claim' କ୍ଲିକ କରନ୍ତୁ। AI ବିଶ୍ଳେଷଣ ତୁରନ୍ତ ଉପଲବ୍ଧ ହେବ।"
    },

    "CLAIM_HISTORY": {
        "en": "To view your submitted claims and history on this website:\n1. Click 'Reports' in the left sidebar navigation (log in first if you haven't already).\n2. On the Reports page, you will see summary metric cards: Total Claims, Normal Review, Medium Review, and High Review.\n3. You can filter claims by review status or search by crop name or location.\n4. Each record displays the crop, claimed loss %, AI predicted disease (MobileNetV2), visual heuristic damage %, review triage status, and submission date.",
        "hi": "इस वेबसाइट पर अपने जमा किए गए दावों का इतिहास देखने के लिए:\n1. बाईं साइडबार में 'Reports' (रिपोर्ट्स) पर क्लिक करें (यदि अभी लॉगिन नहीं हैं तो पहले लॉगिन करें)।\n2. रिपोर्ट्स पेज पर आपको मुख्य सारांश कार्ड दिखेंगे: कुल दावे (Total Claims), सामान्य समीक्षा (Normal Review), मध्यम समीक्षा (Medium Review), और उच्च समीक्षा (High Review)।\n3. आप फसल के नाम या स्थान से खोज सकते हैं और स्थिति के अनुसार फ़िल्टर कर सकते हैं।\n4. प्रत्येक दावे में फसल, दावा किया गया नुकसान %, AI रोग पहचान (MobileNetV2), दृश्य क्षति %, समीक्षा स्थिति और तारीख दिखाई देगी।",
        "mr": "या वेबसाइटवर तुमचे सादर केलेले दावे आणि इतिहास पाहण्यासाठी:\n1. डाव्या बाजूच्या साइडबार मेनूमधील 'Reports' (अहवाल) पर्यायावर क्लिक करा (लॉगिन केले नसेल तर प्रथम लॉगिन करा).\n2. रिपोर्ट्स पृष्ठावर तुम्हाला एकूण दावे (Total Claims), Normal Review, Medium Review आणि High Review सारांश दिसेल.\n3. तुम्ही पिकाच्या नावाने किंवा ठिकाणाने शोधू शकता आणि स्थितीनुसार फिल्टर करू शकता.\n4. प्रत्येक नोंदीमध्ये पीक, नुकसान %, AI रोग निदान (MobileNetV2), दृश्यमान नुकसान % आणि पुनरावलोकन स्थिती दिसेल.",
        "ta": "உங்கள் முந்தைய கோரிக்கைகளைக் காண:\n1. இடது மெனுவில் 'Reports' என்பதைத் திறக்கவும் (உள்நுழையவில்லை என்றால் முதலில் உள்நுழையவும்).\n2. அங்கு மொத்த கோரிக்கைகள், Normal, Medium, High Review எண்ணிக்கை விவரங்கள் இருக்கும்.\n3. தேடல் மற்றும் வடிகட்டி வசதி மூலம் பயிர், AI நோய் கணிப்பு மற்றும் ஆய்வு நிலையை விரிவாகப் பார்க்கலாம்.",
        "te": "మీ మునుపటి క్లెయిమ్‌లను చూడటానికి:\n1. ఎడమ సైడ్‌బార్‌లో 'Reports' పేజీని తెరవండి (లాగిన్ అవ్వకపోతే మొదట లాగిన్ అవ్వండి).\n2. అక్కడ మొత్తం క్లెయిమ్‌లు, Normal, Medium, High Review గణాంకాలు కనిపిస్తాయి.\n3. పంట పేరుతో శోధించి AI వ్యాధి ఫలితాలు మరియు సమీక్ష స్థితిని స్పష్టంగా చూడవచ్చు.",
        "bn": "আপনার পূর্ববর্তী দাবিগুলি দেখতে:\n১. বাম সাইডবারে 'Reports' পৃষ্ঠা খুলুন (লগইন করা না থাকলে প্রথমে লগইন করুন)।\n২. সেখানে মোট দাবি, Normal, Medium ও High Review সারাংশ দেখতে পাবেন।\n৩. ফসল অনুযায়ী অনুসন্ধান করে AI রোগ নির্ণয় ও পর্যালোচনা স্থিতি দেখতে পারবেন।",
        "gu": "તમારા દાવાઓનો ઇતિહાસ જોવા માટે:\n1. ડાબી બાજુના સાઇડબારમાં 'Reports' ખોલો (જો લૉગિન ન હોવ તો પહેલાં લૉગિન કરો).\n2. ત્યાં કુલ દાવા, Normal, Medium અને High Review સારાંશ જોવા મળશે.\n3. પાકના નામથી શોધીને AI પરિણામો અને સમીક્ષા સ્થિતિ જોઈ શકો છો.",
        "kn": "ನಿಮ್ಮ ಹಕ್ಕುಗಳ ಇತಿಹಾಸವನ್ನು ನೋಡಲು:\n1. ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Reports' ಪುಟವನ್ನು ತೆರೆಯಿರಿ (ಮೊದಲು ಲಾಗಿನ್ ಆಗಿ).\n2. ಅಲ್ಲಿ ಒಟ್ಟು ಹಕ್ಕುಗಳು, Normal, Medium, High Review ಸಾರಾಂಶ ಕಾಣಿಸುತ್ತದೆ.\n3. ಬೆಳೆ ಹೆಸರು ಮೂಲಕ ಹುಡುಕಿ AI ರೋಗ ನಿರ್ಣಯ ಮತ್ತು ಪರಿಶೀಲನಾ ಸ್ಥಿತಿಯನ್ನು ವೀಕ್ಷಿಸಬಹುದು.",
        "ml": "നിങ്ങളുടെ ക്ലെയിം ചരിത്രം കാണാൻ:\n1. ഇടത് സൈഡ്ബാറിലെ 'Reports' തുറക്കുക (ആദ്യം ലോഗിൻ ചെയ്യുക).\n2. അവിടെ ആകെ ക്ലെയിമുകൾ, Normal, Medium, High Review വിവരങ്ങൾ കാണാം.\n3. വിള അനുസരിച്ച് തിരഞ്ഞ് AI ഫലങ്ങളും അവലോകന നിലയും പരിശോധിക്കാം.",
        "pa": "ਆਪਣੇ ਦਾਅਵਿਆਂ ਦਾ ਇਤਿਹਾਸ ਦੇਖਣ ਲਈ:\n1. ਖੱਬੇ ਪਾਸੇ 'Reports' ਖੋਲ੍ਹੋ (ਪਹਿਲਾਂ ਲੌਗਇਨ ਕਰੋ)।\n2. ਉੱਥੇ ਕੁੱਲ ਦਾਅਵੇ, Normal, Medium ਅਤੇ High Review ਵੇਰਵੇ ਦਿਖਾਈ ਦੇਣਗੇ।\n3. ਫਸਲ ਮੁਤਾਬਕ ਖੋਜ ਕਰਕੇ AI ਨਤੀਜੇ ਅਤੇ ਸਮੀਖਿਆ ਸਥਿਤੀ ਦੇਖ ਸਕਦੇ ਹੋ।",
        "as": "আপোনাৰ দাবীৰ ইতিহাস চাবলৈ:\n১. বাওঁফালৰ ছাইডবাৰত 'Reports' খোলক (প্ৰথমে লগইন কৰক)।\n২. তাত মুঠ দাবী, Normal, Medium আৰু High Review ৰ তথ্য উপলব্ধ হ'ব।\n৩. শস্যৰ নাম অনুসৰি বিচাৰি AI ফলাফল আৰু স্থিতি চাব পাৰিব।",
        "or": "ଆପଣଙ୍କ ଦାବି ଇତିହାସ ଦେଖିବାକୁ:\n୧. ବାମ ପାର୍ଶ୍ୱରେ 'Reports' ଖୋଲନ୍ତୁ (ପ୍ରଥମେ ଲଗଇନ କରନ୍ତୁ)।\n୨. ସେଠାରେ ମୋଟ ଦାବି, Normal, Medium ଏବଂ High Review ବିବରଣୀ ଦେଖିପାରିବେ।\n୩. ଫସଲ ଅନୁସାରେ ଖୋଜି AI ଫଳାଫଳ ଏବଂ ସ୍ଥିତି ଯାଞ୍ଚ କରିପାରିବେ।"
    },

    "DASHBOARD": {
        "en": "The Dashboard is the central monitoring hub of this website:\n• 📊 Study Area Overview: Select district and observe crop area estimates.\n• 🛰️ Satellite Vegetation Metrics: Displays Sentinel-2 NDVI health values before and after weather events.\n• 📋 Quick Stats: Shows total area analyzed, estimated damaged hectares, and percentage impact.\n• 🛡️ Claim Summary: Quick overview of your recent claims and processing status.\nYou can return to the dashboard anytime by clicking 'Dashboard' at the top of the left sidebar.",
        "hi": "डैशबोर्ड इस वेबसाइट का मुख्य निगरानी केंद्र है:\n• 📊 अध्ययन क्षेत्र सारांश: जिला चुनें और फसल क्षेत्र अनुमान देखें।\n• 🛰️ उपग्रह वनस्पति सूचकांक: आपदा से पहले और बाद के सेंटिनल-2 NDVI मान प्रदर्शित करता है।\n• 📋 त्वरित आंकड़े: कुल विश्लेषित क्षेत्रफल, अनुमानित क्षतिग्रस्त हेक्टेयर और प्रतिशत क्षति।\n• 🛡️ दावा सारांश: आपके हालिया दावों और उनकी समीक्षा स्थिति की त्वरित जानकारी।\nआप बाईं साइडबार में सबसे ऊपर 'Dashboard' पर क्लिक करके कभी भी यहाँ आ सकते हैं।",
        "mr": "डॅशबोर्ड हे या वेबसाइटचे मुख्य निरीक्षण केंद्र आहे:\n• 📊 अभ्यास क्षेत्र आढावा: जिल्हा निवडून पीक क्षेत्राचा अंदाज पहा.\n• 🛰️ उपग्रह वनस्पती निर्देशांक: आपत्तीपूर्वी आणि नंतरची Sentinel-2 NDVI मूल्ये दाखवतो.\n• 📋 सांख्यिकी: एकूण विश्लेषित क्षेत्र, अंदाजे नुकसान झालेले क्षेत्र आणि टक्केवारी.\n• 🛡️ दावा सारांश: तुमच्या अलीकडील दाव्यांची त्वरित माहिती आणि स्थिती.\nडाव्या बाजूच्या साइडबार मेनूमध्ये सर्वात वर असलेल्या 'Dashboard' वर क्लिक करून तुम्ही कधीही येथे येऊ शकता.",
        "ta": "Dashboard என்பது இணையதளத்தின் முதன்மை கண்காணிப்புப் பக்கமாகும்:\n• மாவட்ட பயிர் பரப்பளவு மற்றும் Sentinel-2 NDVI செயற்கைக்கோள் குறியீடுகளைக் காட்டுகிறது.\n• பேரிடருக்கு முந்தைய மற்றும் பிந்தைய பயிர் சேத அளவை அறியலாம்.\n• இடது மெனுவில் 'Dashboard' என்பதை அழுத்தி எப்போது வேண்டுமானாலும் இதைத் திறக்கலாம்.",
        "te": "Dashboard అనేది వెబ్‌సైట్ యొక్క ప్రధాన పర్యవేక్షణ కేంద్రం:\n• జిల్లా పంట విస్తీర్ణం మరియు Sentinel-2 NDVI ఉపగ్రహ సూచికలను ప్రదర్శిస్తుంది.\n• విపత్తుకు ముందు మరియు తరువాత పంట నష్ట శాతాన్ని తెలుసుకోవచ్చు.\n• ఎడమ సైడ్‌బార్‌లో 'Dashboard' క్లిక్ చేసి ఎప్పుడైనా దీన్ని చూడవచ్చు.",
        "bn": "Dashboard হলো এই ওয়েবসাইটের প্রধান পর্যবেক্ষণ কেন্দ্র:\n• জেলার ফসলি জমির ক্ষেত্রফল ও Sentinel-2 NDVI স্যাটেলাইট সূচক প্রদর্শন করে।\n• দুর্যোগের আগে ও পরের ফসলের ক্ষতির পরিমাণ জানা যায়।\n• বাম সাইডবারে 'Dashboard' এ ক্লিক করে যেকোনো সময় এটি খুলতে পারেন।",
        "gu": "Dashboard આ વેબસાઇટનું મુખ્ય મોનિટરિંગ પેજ છે:\n• જિલ્લા પાક વિસ્તાર અને Sentinel-2 NDVI સેટેલાઇટ મૂલ્યો દર્શાવે છે.\n• આપત્તિ પહેલાં અને પછીના નુકસાનની ટકાવારી જાણી શકાય છે.\n• ડાબી બાજુના સાઇડબારમાં 'Dashboard' પર ક્લિક કરીને ગમે ત્યારે આવી શકો છો.",
        "kn": "Dashboard ಈ ವೆಬ್‌ಸೈಟ್‌ನ ಪ್ರಮುಖ ಕೇಂದ್ರವಾಗಿದೆ:\n• ಜಿಲ್ಲೆಯ ಬೆಳೆ ಪ್ರದೇಶ ಮತ್ತು Sentinel-2 NDVI ಉಪಗ್ರಹ ಸೂಚ್ಯಂಕಗಳನ್ನು ಪ್ರದರ್ಶಿಸುತ್ತದೆ.\n• ವಿಪತ್ತಿಗೆ ಮುಂಚಿನ ಮತ್ತು ನಂತರದ ಹಾನಿಯ ಪ್ರಮಾಣವನ್ನು ತಿಳಿಯಬಹುದು.\n• ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Dashboard' ಕ್ಲಿಕ್ ಮಾಡಿ ಯಾವಾಗ ಬೇಕಾದರೂ ವೀಕ್ಷಿಸಬಹುದು.",
        "ml": "Dashboard വെബ്സൈറ്റിന്റെ പ്രധാന നിരീക്ഷണ കേന്ദ്രമാണ്:\n• ജില്ലയിലെ വിള വിസ്തൃതിയും Sentinel-2 NDVI ഉപഗ്രഹ വിവരങ്ങളും കാണിക്കുന്നു.\n• ദുരന്തത്തിന് മുമ്പും ശേഷവുമുള്ള വിളനാശ വിവരങ്ങൾ അറിയാം.\n• ഇടത് സൈഡ്ബാറിലെ 'Dashboard' ക്ലിക്ക് ചെയ്ത് എപ്പോൾ വേണമെങ്കിലും കാണാം.",
        "pa": "Dashboard ਇਸ ਵੈੱਬਸਾਈਟ ਦਾ ਮੁੱਖ ਕੇਂਦਰ ਹੈ:\n• ਜ਼ਿਲ੍ਹੇ ਦੇ ਫਸਲੀ ਰਕਬੇ ਅਤੇ Sentinel-2 NDVI ਸੈਟੇਲਾਈਟ ਅੰਕੜੇ ਦਿਖਾਉਂਦਾ ਹੈ।\n• ਆਫ਼ਤ ਤੋਂ ਪਹਿਲਾਂ ਅਤੇ ਬਾਅਦ ਦੇ ਨੁਕਸਾਨ ਦਾ ਅਨੁਮਾਨ ਦੇਖਿਆ ਜਾ ਸਕਦਾ ਹੈ।\n• ਖੱਬੇ ਪਾਸੇ 'Dashboard' 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਕਿਸੇ ਵੀ ਸਮੇਂ ਖੋਲ੍ਹ ਸਕਦੇ ਹੋ।",
        "as": "Dashboard হ'ল এই ৱেবছাইটৰ মূল নিৰীক্ষণ केंद्र:\n• জিলাৰ শস্য এলেকা আৰু Sentinel-2 NDVI উপগ্ৰহ সূচক প্ৰদৰ্শন কৰে।\n• দুৰ্যোগৰ পূৰ্বৰ আৰু পৰৱৰ্তী ক্ষতিৰ পৰিমাণ জানিব পাৰি।\n• বাওঁফালৰ 'Dashboard' ত ক্লিক কৰি যিকোনো সময়তে চাব পাৰে।",
        "or": "Dashboard ଏହି ୱେବସାଇଟର ପ୍ରମୁଖ ନିରୀକ୍ଷଣ କେନ୍ଦ୍ର:\n• ଜିଲ୍ଲାର ଫସଲ କ୍ଷେତ୍ରଫଳ ଏବଂ Sentinel-2 NDVI ଉପଗ୍ରହ ସୂଚକାଙ୍କ ପ୍ରଦର୍ଶନ କରେ।\n• ବିପର୍ଯ୍ୟୟ ପୂର୍ବ ଏବଂ ପରବର୍ତ୍ତୀ କ୍ଷତିର ଆକଳନ ଜାଣିପାରିବେ।\n• ବାମ ପାର୍ଶ୍ୱରେ 'Dashboard' କ୍ଲିକ କରି ଯେକୌଣସି ସମୟରେ ଏହାକୁ ଦେଖିପାରିବେ।"
    },

    "LOGOUT_LOGGED_IN": {
        "en": "To log out of this website:\nClick the logout button (⎋) located in your User Profile card at the very bottom of the left sidebar, or open your Profile page and click the 'Logout' button. Your session will end immediately and return you to the Dashboard.",
        "hi": "इस वेबसाइट से लॉगआउट करने के लिए:\nबाईं साइडबार में सबसे नीचे आपके प्रोफाइल कार्ड में बने लॉगआउट बटन (⎋) पर क्लिक करें, या Profile पेज खोलकर 'Logout' बटन दबाएं। आपका सत्र समाप्त हो जाएगा।",
        "mr": "या वेबसाइटवरून लॉगआउट करण्यासाठी:\nडाव्या बाजूच्या साइडबार मेनूमध्ये तळाशी असलेल्या प्रोफाइल कार्डमधील लॉगआउट चिन्हावर (⎋) क्लिक करा, किंवा Profile पृष्ठावर जाऊन 'Logout' बटण दाबा. तुमचे सत्र तत्काळ समाप्त होईल.",
        "ta": "வெளியேற (Logout):\nஇடது மெனுவின் கீழே உள்ள பயனர் சுயவிவர அட்டைக்கு அருகில் உள்ள Logout (⎋) பொத்தானை அழுத்தவும் அல்லது Profile பக்கத்தில் உள்ள 'Logout' ஐ அழுத்தவும்.",
        "te": "లాగౌట్ కావడానికి:\nఎడమ సైడ్‌బార్ క్రింద ఉన్న మీ ప్రొఫైల్ కార్డులోని Logout (⎋) బటన్ నొక్కండి లేదా Profile పేజీలోని 'Logout' బటన్ క్లిక్ చేయండి.",
        "bn": "লগআউট করতে:\nবাম সাইডবারের একেবারে নিচে আপনার প্রোফাইল কার্ডের Logout (⎋) বাটনে চাপুন অথবা Profile পৃষ্ঠায় গিয়ে 'Logout' বাটনে ক্লিক করুন।",
        "gu": "લૉગઆઉટ કરવા માટે:\nડાબી બાજુના સાઇડબારમાં નીચે પ્રોફાઇલ કાર્ડમાં Logout (⎋) બટન દબાવો અથવા Profile પેજ પર જઈને 'Logout' કરો.",
        "kn": "ಲಾಗ್‌ಔಟ್ ಮಾಡಲು:\nಎಡ ಸೈಡ್‌ಬಾರ್‌ನ ಕೆಳಭಾಗದಲ್ಲಿರುವ ಪ್ರೊಫೈಲ್ ಕಾರ್ಡ್‌ನಲ್ಲಿ Logout (⎋) ಬಟನ್ ಒತ್ತಿ ಅಥವಾ Profile ಪುಟದಲ್ಲಿ 'Logout' ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "ലോഗൗട്ട് ചെയ്യാൻ:\nഇടത് സൈഡ്ബാറിന്റെ അടിയിലുള്ള പ്രൊഫൈൽ കാർഡിലെ Logout (⎋) ബട്ടൺ അമർത്തുക അല്ലെങ്കിൽ Profile പേജിലെ 'Logout' ക്ലിക്ക് ചെയ്യുക.",
        "pa": "ਲੌਗਆਉਟ ਕਰਨ ਲਈ:\nਖੱਬੇ ਪਾਸੇ ਹੇਠਾਂ ਪ੍ਰੋਫਾਈਲ ਕਾਰਡ ਵਿੱਚ Logout (⎋) ਬਟਨ ਦਬਾਓ ਜਾਂ Profile ਪੰਨੇ 'ਤੇ ਜਾ ਕੇ 'Logout' ਕਰੋ।",
        "as": "লগআউট কৰিবলৈ:\nবাওঁফালৰ ছাইডবাৰৰ তলত থকা প্ৰ'ফাইল কাৰ্ডত Logout (⎋) বুটাম টিপক বা Profile পৃষ্ঠাত 'Logout' ক্লিক কৰক।",
        "or": "ଲଗଆଉଟ୍ କରିବାକୁ:\nବାମ ପାର୍ଶ୍ୱରେ ତଳେ ଥିବା ପ୍ରୋଫାଇଲ କାର୍ଡରେ Logout (⎋) ବଟନ କ୍ଲିକ କରନ୍ତୁ କିମ୍ବା Profile ପୃଷ୍ଠାରେ 'Logout' ଦବାନ୍ତୁ।"
    },

    "LOGOUT_LOGGED_OUT": {
        "en": "You are not currently logged in. Once you log in, you can log out anytime using the logout button (⎋) at the bottom of the left sidebar or from your Profile page.",
        "hi": "आप वर्तमान में लॉगिन नहीं हैं। लॉगिन करने के बाद आप बाईं साइडबार में नीचे दिए गए लॉगआउट बटन (⎋) या Profile पेज से कभी भी लॉगआउट कर सकते हैं।",
        "mr": "तुम्ही सध्या लॉग इन नाही आहात. लॉगिन केल्यानंतर तुम्ही डाव्या बाजूच्या साइडबार मेनूच्या तळाशी असलेल्या लॉगआउट (⎋) बटणाद्वारे किंवा Profile पृष्ठावरून कधीही लॉगआउट करू शकता.",
        "ta": "நீங்கள் தற்போது உள்நுழையவில்லை. உள்நுழைந்த பிறகு, இடது மெனுவின் கீழே உள்ள Logout (⎋) பொத்தான் மூலம் எப்போது வேண்டுமானாலும் வெளியேறலாம்.",
        "te": "మీరు ప్రస్తుతం లాగిన్ అయి లేరు. లాగిన్ అయిన తర్వాత, ఎడమ సైడ్‌బార్ క్రింద ఉన్న Logout (⎋) బటన్ ద్వారా ఎప్పుడైనా లాగౌట్ కావచ్చు.",
        "bn": "আপনি বর্তমানে লগইন নেই। লগইন করার পর, বাম সাইডবারের নিচে Logout (⎋) বাটনের মাধ্যমে যেকোনো সময় লগআউট করতে পারেন।",
        "gu": "તમે હાલમાં લૉગિન નથી. લૉગિન કર્યા પછી, ડાબી બાજુના સાઇડબારમાં નીચે Logout (⎋) બટન દ્વારા ગમે ત્યારે લૉગઆઉટ કરી શકો છો.",
        "kn": "ನೀವು ಪ್ರಸ್ತುತ ಲಾಗಿನ್ ಆಗಿಲ್ಲ. ಲಾಗಿನ್ ಆದ ನಂತರ, ಎಡ ಸೈಡ್‌ಬಾರ್‌ನ ಕೆಳಗಿನ Logout (⎋) ಬಟನ್ ಮೂಲಕ ಯಾವಾಗ ಬೇಕಾದರೂ ಲಾಗ್‌ಔಟ್ ಆಗಬಹುದು.",
        "ml": "നിങ്ങൾ ഇപ്പോൾ ലോഗിൻ ചെയ്തിട്ടില്ല. ലോഗിൻ ചെയ്ത ശേഷം താഴെയുള്ള Logout (⎋) ബട്ടൺ വഴി എപ്പോൾ വേണമെങ്കിലും ലോഗൗട്ട് ചെയ്യാം.",
        "pa": "ਤੁਸੀਂ ਵਰਤਮਾਨ ਵਿੱਚ ਲੌਗਇਨ ਨਹੀਂ ਹੋ। ਲੌਗਇਨ ਕਰਨ ਤੋਂ ਬਾਅਦ ਹੇਠਾਂ Logout (⎋) ਬਟਨ ਰਾਹੀਂ ਕਿਸੇ ਵੀ ਸਮੇਂ ਲੌਗਆਉਟ ਕਰ ਸਕਦੇ ਹੋ।",
        "as": "আপুনি বৰ্তমান লগইন হৈ থকা নাই। লগইন কৰাৰ পিছত তলৰ Logout (⎋) বুটামৰ জৰিয়তে যিকোনো সময়তে লগআউট কৰিব পাৰে।",
        "or": "ଆପଣ ବର୍ତ୍ତମାନ ଲଗଇନ ନାହାଁନ୍ତି। ଲଗଇନ କରିବା ପରେ ତଳେ ଥିବା Logout (⎋) ବଟନ ଦ୍ୱାରା ଯେକୌଣସି ସମୟରେ ଲଗଆଉଟ୍ କରିପାରିବେ।"
    },

    "CLAIM_STATUS_LOGGED_OUT": {
        "en": "To check your claim status, please log in via 'Login / Register' in the left sidebar, then click 'Reports'. Each claim shows an AI review band (NORMAL REVIEW, MEDIUM REVIEW, HIGH REVIEW) to assist human insurance officers.",
        "hi": "अपने दावे की स्थिति देखने के लिए, कृपया बाईं साइडबार में 'Login / Register' से लॉगिन करें और फिर 'Reports' खोलें। प्रत्येक दावे में AI समीक्षा स्थिति (NORMAL, MEDIUM, HIGH REVIEW) दिखाई देती है।",
        "mr": "तुमच्या दाव्याची स्थिती तपासण्यासाठी, कृपया डाव्या बाजूच्या साइडबारमधील 'Login / Register' द्वारे लॉग इन करा आणि नंतर 'Reports' उघडा. प्रत्येक दाव्याची समीक्षा श्रेणी (NORMAL, MEDIUM, HIGH REVIEW) तेथे दिसेल.",
        "ta": "கோரிக்கை நிலையை அறிய, இடது மெனுவில் 'Login / Register' மூலம் உள்நுழைந்து 'Reports' பக்கத்தைத் திறக்கவும். அங்கு NORMAL, MEDIUM, HIGH ஆய்வு நிலைகள் காட்டப்படும்.",
        "te": "క్లెయిమ్ స్థితి తెలుసుకోవడానికి, ఎడమ సైడ్‌బార్‌లో 'Login / Register' ద్వారా లాగిన్ అయి 'Reports' తెరవండి. అక్కడ NORMAL, MEDIUM, HIGH సమీక్ష స్థితులు ఉంటాయి.",
        "bn": "দাবীর স্থিতি জানতে, বাম সাইডবারে 'Login / Register' দিয়ে লগইন করে 'Reports' খুলুন। সেখানে NORMAL, MEDIUM, HIGH পর্যালোচনা স্থিতি দেখা যাবে।",
        "gu": "દાવાની સ્થિતિ જાણવા માટે, ડાબી બાજુના સાઇડબારમાં 'Login / Register' થી લૉગિન કરીને 'Reports' ખોલો. ત્યાં NORMAL, MEDIUM, HIGH સમીક્ષા સ્થિતિ દેખાશે.",
        "kn": "ಹಕ್ಕಿನ ಸ್ಥಿತಿಯನ್ನು ತಿಳಿಯಲು, ಎಡ ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ 'Login / Register' ಮೂಲಕ ಲಾಗಿನ್ ಆಗಿ 'Reports' ತೆರೆಯಿರಿ. ಅಲ್ಲಿ NORMAL, MEDIUM, HIGH ಪರಿಶೀಲನಾ ಸ್ಥಿತಿ ಇರುತ್ತದೆ.",
        "ml": "ക്ലെയിം നില അറിയാൻ, ഇടത് സൈഡ്ബാറിലെ 'Login / Register' വഴി ലോഗിൻ ചെയ്ത് 'Reports' തുറക്കുക. NORMAL, MEDIUM, HIGH നിലകൾ അവിടെ കാണാം.",
        "pa": "ਦਾਅਵੇ ਦੀ ਸਥਿਤੀ ਦੇਖਣ ਲਈ, ਖੱਬੇ ਪਾਸੇ 'Login / Register' ਰਾਹੀਂ ਲੌਗਇਨ ਕਰਕੇ 'Reports' ਖੋਲ੍ਹੋ। ਉੱਥੇ NORMAL, MEDIUM, HIGH ਸਮੀਖਿਆ ਸਥਿਤੀ ਦਿਖਾਈ ਦੇਵੇਗੀ।",
        "as": "দাবীৰ স্থিতি জানিবলৈ, বাওঁফালৰ 'Login / Register' ৰে লগইন কৰি 'Reports' খোলক। তাত NORMAL, MEDIUM, HIGH পৰ্যালোচনা স্থিতি দেখিব।",
        "or": "ଦାବି ସ୍ଥିତି ଜାଣିବାକୁ, ବାମ ପାର୍ଶ୍ୱରେ 'Login / Register' ଦ୍ୱାରା ଲଗଇନ କରି 'Reports' ଖୋଲନ୍ତୁ। ସେଠାରେ NORMAL, MEDIUM, HIGH ସମୀକ୍ଷା ସ୍ଥିତି ଦେଖାଯିବ।"
    },

    "PROFILE_LOGGED_IN": {
        "en": "Your Profile details:\n• Name: {name}\n• Username: {username}\n• State: {state}\n• District: {district}\n\nTo view or update your profile details:\nClick on your User Profile card at the very bottom of the left sidebar. On the Profile page, you can see your registration details and click 'Edit Profile' to update your name, phone, email, state, or district.",
        "hi": "आपकी प्रोफाइल जानकारी:\n• नाम: {name}\n• यूज़रनेम: {username}\n• राज्य: {state}\n• जिला: {district}\n\nप्रोफाइल देखने या संपादित करने के लिए:\nबाईं साइडबार में सबसे नीचे अपने प्रोफाइल कार्ड पर क्लिक करें। Profile पेज पर आप अपनी जानकारी देख सकते हैं और 'Edit Profile' पर क्लिक करके नाम, मोबाइल, ईमेल, राज्य या जिला बदल सकते हैं।",
        "mr": "तुमची प्रोफाइल माहिती:\n• नाव: {name}\n• वापरकर्तानाव: {username}\n• राज्य: {state}\n• जिल्हा: {district}\n\nप्रोफाइल पाहण्यासाठी किंवा बदलण्यासाठी:\nडाव्या बाजूच्या साइडबार मेनूमध्ये सर्वात खाली तुमच्या प्रोफाइल कार्डवर क्लिक करा. Profile पृष्ठावर तुम्ही तुमची माहिती पाहू शकता आणि 'Edit Profile' वर क्लिक करून आवश्यक बदल करू शकता.",
        "ta": "உங்கள் சுயவிவரம்:\n• பெயர்: {name} | பயனர்பெயர்: {username}\n• மாநிலம்: {state} | மாவட்டம்: {district}\nசுயவிவரத்தை மாற்ற இடது மெனுவின் கீழே உள்ள சுயவிவர அட்டையை அழுத்தி 'Edit Profile' என்பதைத் தேர்ந்தெடுக்கவும்.",
        "te": "మీ ప్రొఫైల్ వివరాలు:\n• పేరు: {name} | యూజర్‌నేమ్: {username}\n• రాష్ట్రం: {state} | జిల్లా: {district}\nవివరాలు సవరించడానికి ఎడమ సైడ్‌బార్ క్రింద ఉన్న ప్రొఫైల్ కార్డుపై క్లిక్ చేసి 'Edit Profile' ఎంచుకోండి.",
        "bn": "আপনার প্রোফাইল বিবরণ:\n• নাম: {name} | ব্যবহারকারী: {username}\n• রাজ্য: {state} | জেলা: {district}\nপ্রোফাইল পরিবর্তন করতে বাম সাইডবারের নিচে প্রোফাইল কার্ডে ক্লিক করে 'Edit Profile' বাছুন।",
        "gu": "તમારી પ્રોફાઇલ વિગતો:\n• નામ: {name} | વપરાશકર્તાનામ: {username}\n• રાજ્ય: {state} | જિલ્લો: {district}\nવિગતો બદલવા માટે ડાબી બાજુના સાઇડબારમાં નીચે પ્રોફાઇલ કાર્ડ પર ક્લિક કરીને 'Edit Profile' પસંદ કરો.",
        "kn": "ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ವಿವರಗಳು:\n• ಹೆಸರು: {name} | ಬಳಕೆದಾರ ಹೆಸರು: {username}\n• ರಾಜ್ಯ: {state} | ಜಿಲ್ಲೆ: {district}\nವಿವರಗಳನ್ನು ನವೀಕರಿಸಲು ಎಡ ಸೈಡ್‌ಬಾರ್‌ನ ಕೆಳಗಿನ ಪ್ರೊಫೈಲ್ ಕಾರ್ಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ 'Edit Profile' ಆಯ್ಕೆಮಾಡಿ.",
        "ml": "നിങ്ങളുടെ പ്രൊഫൈൽ വിവരങ്ങൾ:\n• പേര്: {name} | യൂസർനെയിം: {username}\n• സംസ്ഥാനം: {state} | ജില്ല: {district}\nവിവരങ്ങൾ മാറ്റാൻ താഴെയുള്ള പ്രൊഫൈൽ കാർഡിൽ ക്ലിക്ക് ചെയ്ത് 'Edit Profile' തിരഞ്ഞെടുക്കുക.",
        "pa": "ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਜਾਣਕਾਰੀ:\n• ਨਾਮ: {name} | ਯੂਜ਼ਰਨੇਮ: {username}\n• ਰਾਜ: {state} | ਜ਼ਿਲ੍ਹਾ: {district}\nਵੇਰਵੇ ਬਦਲਣ ਲਈ ਖੱਬੇ ਪਾਸੇ ਹੇਠਾਂ ਪ੍ਰੋਫਾਈਲ ਕਾਰਡ 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ 'Edit Profile' ਚੁਣੋ।",
        "as": "আপোনাৰ প্ৰ'ফাইল তথ্য:\n• নাম: {name} | ইউজাৰনেম: {username}\n• ৰাজ্য: {state} | জিলা: {district}\nতথ্য সলনি কৰিবলৈ বাওঁফালৰ তলত থকা প্ৰ'ফাইল কাৰ্ডত ক্লিক কৰি 'Edit Profile' বাছক।",
        "or": "ଆପଣଙ୍କ ପ୍ରୋଫାଇଲ ବିବରଣୀ:\n• ନାମ: {name} | ୟୁଜରନେମ: {username}\n• ରାଜ୍ୟ: {state} | ଜିଲ୍ଲା: {district}\nବିବରଣୀ ସଂଶୋଧନ ପାଇଁ ବାମ ପାର୍ଶ୍ୱରେ ତଳେ ଥିବା ପ୍ରୋଫାଇଲ କାର୍ଡ କ୍ଲିକ କରି 'Edit Profile' ବାଛନ୍ତୁ।"
    },

    "PROFILE_LOGGED_OUT": {
        "en": "To view your profile, please log in first by clicking 'Login / Register' in the left sidebar. Once logged in, your profile card will appear at the bottom of the sidebar, where you can view and edit your profile details.",
        "hi": "अपनी प्रोफाइल देखने के लिए, कृपया पहले बाईं साइडबार में 'Login / Register' पर क्लिक करके लॉगिन करें। लॉगिन के बाद साइडबार में नीचे आपका प्रोफाइल कार्ड दिखाई देगा, जहां से आप अपनी जानकारी देख और बदल सकते हैं।",
        "mr": "तुमची प्रोफाइल पाहण्यासाठी, कृपया प्रथम डाव्या बाजूच्या साइडबारमधील 'Login / Register' पर्यायावर क्लिक करून लॉग इन करा. लॉगिन केल्यानंतर मेनूच्या तळाशी तुमचे प्रोफाइल कार्ड दिसेल, जिथून तुम्ही माहिती पाहू आणि बदलू शकता.",
        "ta": "சுயவிவரத்தைக் காண முதலில் 'Login / Register' மூலம் உள்நுழையவும். உள்நுழைந்த பிறகு, இடது மெனுவின் கீழே உங்கள் சுயவிவர அட்டை தோன்றும்.",
        "te": "మీ ప్రొఫైల్ చూడటానికి మొదట 'Login / Register' ద్వారా లాగిన్ అవ్వండి. లాగిన్ అయిన తర్వాత ఎడమ సైడ్‌బార్ క్రింద మీ ప్రొఫైల్ కార్డు కనిపిస్తుంది.",
        "bn": "প্রোফাইল দেখতে প্রথমে 'Login / Register' দিয়ে লগইন করুন। লগইন করার পর বাম সাইডবারের নিচে প্রোফাইল কার্ড দেখতে পাবেন।",
        "gu": "પ્રોફાઇલ જોવા માટે પહેલાં 'Login / Register' થી લૉગિન કરો. લૉગિન કર્યા પછી ડાબી બાજુના સાઇડબારમાં નીચે પ્રોફાઇલ કાર્ડ દેખાશે.",
        "kn": "ಪ್ರೊಫೈಲ್ ನೋಡಲು ಮೊದಲು 'Login / Register' ಮೂಲಕ ಲಾಗಿನ್ ಆಗಿ. ಲಾಗಿನ್ ಆದ ನಂತರ ಎಡ ಸೈಡ್‌ಬಾರ್‌ನ ಕೆಳಗೆ ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಕಾರ್ಡ್ ಕಾಣಿಸುತ್ತದೆ.",
        "ml": "പ്രൊഫൈൽ കാണാൻ ആദ്യം 'Login / Register' വഴി ലോഗിൻ ചെയ്യുക. ശേഷം ഇടത് സൈഡ്ബാറിന്റെ അടിയിൽ പ്രൊഫൈൽ കാർഡ് കാണാം.",
        "pa": "ਪ੍ਰੋਫਾਈਲ ਦੇਖਣ ਲਈ ਪਹਿਲਾਂ 'Login / Register' ਰਾਹੀਂ ਲੌਗਇਨ ਕਰੋ। ਲੌਗਇਨ ਕਰਨ ਤੋਂ ਬਾਅਦ ਹੇਠਾਂ ਤੁਹਾਡਾ ਪ੍ਰੋਫਾਈਲ ਕਾਰਡ ਦਿਖਾਈ ਦੇਵੇਗਾ।",
        "as": "প্ৰ'ফাইল চাবলৈ প্ৰথমে 'Login / Register' ৰে লগইন কৰক। লগইন কৰাৰ পিছত তলত আপোনাৰ প্ৰ'ফাইল কাৰ্ড দেখা যাব।",
        "or": "ପ୍ରୋଫାଇଲ ଦେଖିବାକୁ ପ୍ରଥମେ 'Login / Register' ଦ୍ୱାରା ଲଗଇନ କରନ୍ତୁ। ଲଗଇନ ପରେ ତଳେ ଆପଣଙ୍କ ପ୍ରୋଫାଇଲ କାର୍ଡ ଦେଖାଯିବ।"
    },

    "ABOUT_PROJECT": {
        "en": "About this PMFBY Crop Damage Detection & Claim Verification Project:\nThis website is an AI and satellite-assisted agricultural insurance demonstration platform featuring:\n1. 🛡️ Insurance Claim: Submit crop damage details and field photos.\n2. 🔬 Deep Learning (MobileNetV2): Classifies plant diseases and crop conditions from uploaded photos.\n3. 🔍 Visual Heuristic Damage Estimation: Measures visible discolouration and tissue loss percentage.\n4. 🛰️ Satellite Earth Observation: Analyzes European Space Agency Sentinel-2 imagery via Google Earth Engine to compute NDVI vegetation loss across the district.\n5. 🌦️ Weather Verification: Cross-references ERA5-Land historical weather anomalies (rainfall & temperature) during disaster dates.\n6. ⚖️ Claim Risk Triage: Categorizes claims into Normal, Medium, or High Review for objective, transparent human officer audit.",
        "hi": "इस PMFBY फसल क्षति पहचान व दावा सत्यापन प्रोजेक्ट के बारे में:\nयह वेबसाइट एक AI और उपग्रह-सहायता प्राप्त कृषि बीमा प्रदर्शन प्लेटफॉर्म है, जिसमें शामिल हैं:\n1. 🛡️ बीमा दावा (Insurance Claim): फसल नुकसान और खेत की फोटो सबमिट करें।\n2. 🔬 डीप लर्निंग (MobileNetV2): अपलोड की गई फोटो से फसल रोग और स्थिति की पहचान।\n3. 🔍 दृश्य क्षति अनुमान: पौधे की पत्तियों पर दिखाई देने वाले नुकसान का प्रतिशत आकलन।\n4. 🛰️ उपग्रह अवलोकन: गूगल अर्थ इंजन और सेंटिनल-2 उपग्रह द्वारा जिले भर में NDVI वनस्पति हानि की माप।\n5. 🌦️ मौसम सत्यापन: आपदा की तारीखों के दौरान ERA5-Land बारिश और तापमान विसंगतियों की जांच।\n6. ⚖️ क्लेम रिस्क ट्रायज: दावों को Normal, Medium या High Review में वर्गीकृत करना ताकि मानव अधिकारी निष्पक्ष निर्णय ले सकें।",
        "mr": "या PMFBY पीक नुकसान शोध व दावा पडताळणी प्रकल्पाबद्दल:\nही वेबसाइट एक AI आणि उपग्रह-साहाय्यित कृषी विमा प्रात्यक्षिक प्लॅटफॉर्म आहे:\n1. 🛡️ विमा दावा: पिकाचे नुकसान आणि शेतातील फोटो सादर करा.\n2. 🔬 डीप लर्निंग (MobileNetV2): फोटोवरून पिकाचे रोग आणि आरोग्य स्थिती ओळखणे.\n3. 🔍 दृश्यमान नुकसान अंदाज: पानांवरील प्रत्यक्ष नुकसानीची टक्केवारी मोजणे.\n4. 🛰️ उपग्रह निरीक्षण: Google Earth Engine आणि Sentinel-2 उपग्रहाद्वारे NDVI वनस्पती नुकसान मोजणे.\n5. 🌦️ हवामान पडताळणी: ERA5-Land द्वारे आपत्ती काळातील पाऊस आणि तापमानातील तफावत तपासणे.\n6. ⚖️ क्लेम रिस्क ट्रायज: दाव्यांचे Normal, Medium किंवा High Review मध्ये वर्गीकरण करून मानवी अधिकाऱ्यांना पारदर्शक तपासणीत मदत करणे.",
        "ta": "இந்த PMFBY திட்டம் பற்றி:\nஇது செயற்கை நுண்ணறிவு மற்றும் செயற்கைக்கோள் தரவு மூலம் பயிர் சேதத்தை மதிப்பீடு செய்யும் தளமாகும். MobileNetV2 நோய் கணிப்பு, Sentinel-2 NDVI செயற்கைக்கோள் பகுப்பாய்வு மற்றும் ERA5 வானிலை சரிபார்ப்பு மூலம் காப்பீட்டு அதிகாரிகளுக்கு வெளிப்படையான ஆய்வு முன்னுரிமைகளை வழங்குகிறது.",
        "te": "ఈ PMFBY ప్రాజెక్ట్ గురించి:\nఇది AI మరియు ఉపగ్రహ డేటా ఆధారిత పంట నష్ట అంచనా ప్లాట్‌ఫారమ్. MobileNetV2 రోగ నిర్ధారణ, Sentinel-2 NDVI ఉపగ్రహ విశ్లేషణ మరియు ERA5 వాతావరణ ధృవీకరణ ద్వారా క్లెయిమ్‌లను Normal, Medium, High Review వర్గాలుగా విభజిస్తుంది.",
        "bn": "এই PMFBY প্রকল্প সম্পর্কে:\nএটি একটি AI এবং স্যাটেলাইট-সহায়তাপ্রাপ্ত ফসল ক্ষতি মূল্যায়ন প্ল্যাটফর্ম। MobileNetV2 রোগ নির্ণয়, Sentinel-2 NDVI উপগ্রহ বিশ্লেষণ এবং ERA5 আবহাওয়া যাচাইকরণের মাধ্যমে কর্মকর্তাদের স্বচ্ছ পর্যালোচনায় সহায়তা করে।",
        "gu": "આ PMFBY પ્રોજેક્ટ વિશે:\nઆ AI અને સેટેલાઇટ-આધારિત પાક નુકસાન મૂલ્યાંકન પ્લેટફોર્મ છે. MobileNetV2 રોગ અનુમાન, Sentinel-2 NDVI સેટેલાઇટ વિશ્લેષણ અને ERA5 હવામાન ચકાસણી દ્વારા પારદર્શક સમીક્ષા પૂરી પાડે છે.",
        "kn": "ಈ PMFBY ಯೋಜನೆಯ ಬಗ್ಗೆ:\nಇದು AI ಮತ್ತು ಉಪಗ್ರಹ ಆಧಾರಿತ ಬೆಳೆ ಹಾನಿ ಪತ್ತೆ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಆಗಿದೆ. MobileNetV2 ರೋಗ ಪತ್ತೆ, Sentinel-2 NDVI ಉಪಗ್ರಹ ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ERA5 ಹವಾಮಾನ ಪರಿಶೀಲನೆ ಮೂಲಕ ವಿಮಾ ಅಧಿಕಾರಿಗಳಿಗೆ ಪಾರದರ್ಶಕ ಪರಿಶೀಲನೆಗೆ ನೆರವಾಗುತ್ತದೆ.",
        "ml": "ഈ PMFBY പ്രോജക്റ്റിനെക്കുറിച്ച്:\nഇതൊരു AI, ഉപഗ്രഹ അധിഷ്ഠിത വിളനാശ വിലയിരുത്തൽ സംവിധാനമാണ്. MobileNetV2 രോഗനിർണ്ണയം, Sentinel-2 NDVI വിശകലനം, ERA5 കാലാവസ്ഥാ പരിശോധന എന്നിവ ഇതിലുണ്ട്.",
        "pa": "ਇਸ PMFBY ਪ੍ਰੋਜੈਕਟ ਬਾਰੇ:\nਇਹ ਇੱਕ AI ਅਤੇ ਸੈਟੇਲਾਈਟ ਅਧਾਰਿਤ ਫਸਲ ਨੁਕਸਾਨ ਮੁਲਾਂਕਣ ਪਲੇਟਫਾਰਮ ਹੈ। MobileNetV2 ਬਿਮਾਰੀ ਜਾਂਚ, Sentinel-2 NDVI ਸੈਟੇਲਾਈਟ ਵਿਸ਼ਲੇਸ਼ਣ ਅਤੇ ERA5 ਮੌਸਮ ਜਾਂਚ ਰਾਹੀਂ ਦਾਅਵਿਆਂ ਦੀ ਪਾਰਦਰਸ਼ੀ ਸਮੀਖਿਆ ਕਰਦਾ ਹੈ।",
        "as": "এই PMFBY প্ৰকল্পৰ বিষয়ে:\nই এটা AI আৰু উপগ্ৰহভিত্তিক শস্য ক্ষতি নিৰ্ণয় প্লেটফৰ্ম। MobileNetV2 ৰোগ নিৰ্ণয়, Sentinel-2 NDVI উপগ্ৰহ বিশ্লেষণ আৰু ERA5 বতৰ পৰীক্ষণৰ সুবিধা ইয়াত আছে।",
        "or": "ଏହି PMFBY ପ୍ରୋଜେକ୍ଟ ବିଷୟରେ:\nଏହା ଏକ AI ଏବଂ ଉପଗ୍ରହ ଆଧାରିତ ଫସଲ କ୍ଷତି ମୂଲ୍ୟାଙ୍କନ ପ୍ଲାଟଫର୍ମ। MobileNetV2 ରୋଗ ନିର୍ଣ୍ଣୟ, Sentinel-2 NDVI ଉପଗ୍ରହ ବିଶ୍ଳେଷଣ ଏବଂ ERA5 ପାଣିପାଗ ଯାଞ୍ଚ ଏଥିରେ ସାମିଲ ଅଛି।"
    },

    "SATELLITE_NDVI": {
        "en": "Normalized Difference Vegetation Index (NDVI) & Satellite Analysis:\n• Optical Sensor: European Space Agency Sentinel-2 satellite imagery processed via Google Earth Engine.\n• Formula: NDVI = (NIR - Red) / (NIR + Red). Values range from -1.0 to +1.0.\n• Crop Interpretation: Dense, healthy green vegetation typically scores between 0.4 and 0.8. Severely damaged, flooded, or drought-stricken crops drop towards 0.0 to 0.2.\n• Disaster Comparison: Compares mean district NDVI before and after the event date to calculate broad-scale vegetation loss %, providing independent, tamper-proof satellite evidence.",
        "hi": "NDVI और उपग्रह विश्लेषण की जानकारी:\n• उपग्रह सेंसर: यूरोपीय अंतरिक्ष एजेंसी सेंटिनल-2 उपग्रह डेटा, गूगल अर्थ इंजन द्वारा संसाधित।\n• सूत्र: NDVI = (NIR - Red) / (NIR + Red)। इसका मान -1.0 से +1.0 तक होता है।\n• फसल स्वास्थ्य: स्वस्थ हरी फसल का NDVI 0.4 से 0.8 के बीच होता है। बाढ़, सूखे या बीमारी से क्षतिग्रस्त फसल का NDVI घटकर 0.0 से 0.2 तक गिर जाता है।\n• आपदा तुलना: आपदा से पहले और बाद के NDVI की तुलना करके जिले भर में वनस्पति क्षति प्रतिशत की गणना की जाती है।",
        "mr": "NDVI आणि उपग्रह विश्लेषणाबद्दल माहिती:\n• उपग्रह सेन्सर: युरोपियन स्पेस एजन्सीचा Sentinel-2 उपग्रह डेटा, Google Earth Engine द्वारे विश्लेषित.\n• सूत्र: NDVI = (NIR - Red) / (NIR + Red). मूल्ये -१.० ते +१.० दरम्यान असतात.\n• पीक आरोग्य: निरोगी हिरव्या पिकांचे NDVI साधारण ०.४ ते ०.८ असते. पूर, दुष्काळ किंवा रोगामुळे नुकसान झाल्यास ते ०.० ते ०.२ पर्यंत खाली येते.\n• आपत्ती तुलना: आपत्तीपूर्वीची आणि नंतरची तुलना करून संपूर्ण जिल्ह्यातील वनस्पती हानीची टक्केवारी पारदर्शकपणे काढली जाते.",
        "ta": "NDVI மற்றும் செயற்கைக்கோள் பகுப்பாய்வு:\nSentinel-2 செயற்கைக்கோள் மூலம் NDVI (தாவர குறியீடு) கணக்கிடப்படுகிறது. ஆரோக்கியமான பயிர்களின் NDVI 0.4 முதல் 0.8 வரை இருக்கும். பேரிடரால் பாதிக்கப்பட்ட பயிர்களின் குறியீடு குறையும்.",
        "te": "NDVI మరియు ఉపగ్రహ విశ్లేషణ:\nSentinel-2 ఉపగ్రహం ద్వారా NDVI వృక్ష సూచిక లెక్కిస్తారు. ఆరోగ్యకరమైన పంటలకు NDVI 0.4 నుండి 0.8 వరకు ఉంటుంది. విపత్తు వలన పంట దెబ్బతింటే ఈ విలువ తగ్గుతుంది.",
        "bn": "NDVI এবং উপগ্রহ বিশ্লেষণ:\nSentinel-2 স্যাটেলাইটের মাধ্যমে NDVI সূচক নির্ণয় করা হয়। সুস্থ ফসলের NDVI ০.৪ থেকে ০.৮ হয়। দুর্যোগে ক্ষতিগ্রস্ত হলে এই মান হ্রাস পায়।",
        "gu": "NDVI અને સેટેલાઇટ વિશ્લેષણ:\nSentinel-2 સેટેલાઇટ દ્વારા NDVI સૂચકાંક માપવામાં આવે છે. સ્વસ્થ પાક માટે NDVI 0.4 થી 0.8 હોય છે, જ્યારે નુકસાનગ્રસ્ત પાકમાં તે ઘટી જાય છે.",
        "kn": "NDVI ಮತ್ತು ಉಪಗ್ರಹ ವಿಶ್ಲೇಷಣೆ:\nSentinel-2 ಉಪಗ್ರಹದ ಮೂಲಕ NDVI ಸಸ್ಯವರ್ಗದ ಸೂಚ್ಯಂಕವನ್ನು ಅಳೆಯಲಾಗುತ್ತದೆ. ಆರೋಗ್ಯಕರ ಬೆಳೆಗೆ NDVI 0.4 ರಿಂದ 0.8 ಇರುತ್ತದೆ. ಹಾನಿಗೊಳಗಾದಾಗ ಈ ಮೌಲ್ಯ ಕಡಿಮೆಯಾಗುತ್ತದೆ.",
        "ml": "NDVI ഉപഗ്രഹ വിശകലനം:\nSentinel-2 ഉപഗ്രഹം വഴിയാണ് NDVI അളക്കുന്നത്. നല്ല വിളകൾക്ക് NDVI 0.4 മുതൽ 0.8 വരെയാണ്. വിളനാശമുണ്ടാകുമ്പോൾ ഈ മൂല്യം കുറയുന്നു.",
        "pa": "NDVI ਅਤੇ ਸੈਟੇਲਾਈਟ ਵਿਸ਼ਲੇਸ਼ਣ:\nSentinel-2 ਸੈਟੇਲਾਈਟ ਰਾਹੀਂ NDVI ਸੂਚਕਾਂਕ ਮਾਪਿਆ ਜਾਂਦਾ ਹੈ। ਤੰਦਰੁਸਤ ਫਸਲ ਦਾ NDVI 0.4 ਤੋਂ 0.8 ਹੁੰਦਾ ਹੈ, ਜਦਕਿ ਨੁਕਸਾਨ ਹੋਣ 'ਤੇ ਇਹ ਘਟ ਜਾਂਦਾ ਹੈ।",
        "as": "NDVI আৰু উপগ্ৰহ বিশ্লেষণ:\nSentinel-2 উপগ্ৰহৰ দ্বাৰা NDVI সূচক নিৰ্ণয় কৰা হয়। সুস্থ শস্যৰ NDVI ০.৪ ৰ পৰা ০.৮ হয়। ক্ষতি হ'লে ইয়াৰ মান হ্রাস পায়।",
        "or": "NDVI ଏବଂ ଉପଗ୍ରହ ବିଶ୍ଳେଷଣ:\nSentinel-2 ଉପଗ୍ରହ ମାଧ୍ୟମରେ NDVI ମପାଯାଏ। ସୁସ୍ଥ ଫସଲ ପାଇଁ NDVI ୦.୪ ରୁ ୦.୮ ଥାଏ। କ୍ଷତିଗ୍ରସ୍ତ ହେଲେ ଏହି ମୂଲ୍ୟ କମିଯାଏ।"
    },

    "AI_RESULT": {
        "en": "Understanding Claim Verification Results:\n1. 🔬 AI Disease Prediction (MobileNetV2): Deep neural network trained on plant pathology datasets to identify specific crop diseases, blights, or healthy conditions.\n2. 🔍 Visual Heuristic Estimate: A computer vision algorithm that calculates the percentage of visible tissue discolouration/necrosis on the uploaded farm photo as supporting evidence.\n3. 🌦️ Weather Verification: Cross-checks ERA5-Land meteorological records to confirm if abnormal rainfall or temperature coincided with the loss event.\n4. ⚖️ Review Triage (NORMAL, MEDIUM, HIGH): ML classifier that prioritizes claims for officer inspection.\nIMPORTANT: This AI system assists transparent claim audits; it does not automatically reject claims or determine final financial payouts.",
        "hi": "दावा सत्यापन परिणामों को समझना:\n1. 🔬 AI रोग पहचान (MobileNetV2): डीप लर्निंग मॉडल जो अपलोड की गई फोटो से विशिष्ट फसल रोग या स्वस्थ स्थिति की पहचान करता है।\n2. 🔍 दृश्य क्षति अनुमान: कंप्यूटर विज़न एल्गोरिदम जो फोटो से पत्तियों के रंग परिवर्तन और क्षति प्रतिशत की गणना करता है।\n3. 🌦️ मौसम सत्यापन: ERA5-Land डेटा द्वारा जांचता है कि क्या आपदा के समय असामान्य बारिश या तापमान दर्ज हुआ था।\n4. ⚖️ समीक्षा प्राथमिकता (NORMAL, MEDIUM, HIGH): मानव अधिकारी के निरीक्षण हेतु दावों को प्राथमिकता देता है।\nमहत्वपूर्ण: यह AI प्रणाली अधिकारियों की सहायता के लिए है; यह स्वचालित रूप से दावे को अस्वीकार या भुगतान निर्धारित नहीं करती।",
        "mr": "दावा पडताळणी निकाल समजून घेणे:\n1. 🔬 AI रोग निदान (MobileNetV2): फोटोवरून पिकाचा विशिष्ट रोग किंवा निरोगी स्थिती ओळखणारे डीप लर्निंग मॉडेल.\n2. 🔍 दृश्यमान नुकसान अंदाज: फोटोवरील पानांचा रंगबदल आणि प्रत्यक्ष नुकसान टक्केवारी मोजणारा अल्गोरिदम.\n3. 🌦️ हवामान पडताळणी: आपत्तीच्या काळात असामान्य पाऊस किंवा तापमान होते का हे तपासते.\n4. ⚖️ पुनरावलोकन ट्रायज (NORMAL, MEDIUM, HIGH): अधिकाऱ्यांच्या तपासणीसाठी प्राधान्यक्रम ठरवणारी प्रणाली.\nमहत्त्वाचे: ही AI प्रणाली पारदर्शक तपासणीसाठी सहाय्यक आहे; अंतिम विमा निर्णय अधिकृत मानवी अधिकारीच घेतात.",
        "ta": "AI முடிவுகள் விளக்கம்:\n1. MobileNetV2 பயிர் நோயை அடையாளம் காண்கிறது.\n2. காட்சி சேத மதிப்பீடு புகைப்படத்திலிருந்து சேத சதவீதத்தைக் கணக்கிடுகிறது.\n3. வானிலை சரிபார்ப்பு பேரிடர் கால வானிலையை உறுதி செய்கிறது.\n4. மனித அதிகாரியே இறுதி காப்பீட்டு முடிவை எடுப்பார்.",
        "te": "AI ఫలితాల వివరణ:\n1. MobileNetV2 పంట తెగుళ్లను గుర్తిస్తుంది.\n2. విజువల్ నష్టం అంచనా ఫోటో నుండి నష్ట శాతాన్ని లెక్కిస్తుంది.\n3. వాతావరణ ధృవీకరణ వర్షపాతం/ఉష్ణోగ్రతను సరిపోల్చుతుంది.\n4. తుది నిర్ణయాన్ని మానవ అధికారే తీసుకుంటారు.",
        "bn": "AI ফলাফল ব্যাখ্যা:\n১. MobileNetV2 ফসলের রোগ নির্ণয় করে।\n২. ভিজ্যুয়াল ক্ষতি অনুমান ছবি থেকে ক্ষতির % পরিমাপ করে।\n৩. আবহাওয়া যাচাইকরণ দুর্যোগকালীন আবহাওয়া পরীক্ষা করে।\n৪. মানব কর্মকর্তাই চূড়ান্ত বিমা সিদ্ধান্ত নেন।",
        "gu": "AI પરિણામોની સમજણ:\n1. MobileNetV2 પાક રોગ ઓળખે છે.\n2. વિઝ્યુઅલ નુકસાન અંદાજ ફોટો પરથી નુકસાનની % ગણે છે.\n3. હવામાન ચકાસણી વરસાદ અને તાપમાનની વિસંગતતા તપાસે છે.\n4. અંતિમ નિર્ણય માનવ અધિકારી જ લે છે.",
        "kn": "AI ಫಲಿತಾಂಶಗಳ ವಿವರಣೆ:\n1. MobileNetV2 ಬೆಳೆ ರೋಗವನ್ನು ಪತ್ತೆ ಮಾಡುತ್ತದೆ.\n2. ದೃಶ್ಯ ಹಾನಿ ಅಂದಾಜು ಫೋಟೋದಿಂದ ಹಾನಿಯ % ಲೆಕ್ಕಾಚಾರ ಮಾಡುತ್ತದೆ.\n3. ಹವಾಮಾನ ಪರಿಶೀಲನೆ ಮಳೆ અને ತಾಪಮಾನವನ್ನು ತಾಳೆ ನೋಡುತ್ತದೆ.\n4. ಅಂತಿಮ ನಿರ್ಧಾರವನ್ನು ಮಾನವ ಅಧಿಕಾರಿಯೇ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ.",
        "ml": "AI ഫലങ്ങളുടെ വിശദീകരണം:\n1. MobileNetV2 വിള രോഗങ്ങൾ കണ്ടെത്തുന്നു.\n2. വിഷ്വൽ കേടുപാടുകൾ ഫോട്ടോയിൽ നിന്ന് നഷ്ട % കണക്കാക്കുന്നു.\n3. കാലാവസ്ഥാ പരിശോധന അസാധാരണ മഴ/താപനില സ്ഥിരീകരിക്കുന്നു.\n4. അന്തിമ തീരുമാനം മനുഷ്യ ഉദ്യോഗസ്ഥൻ എടുക്കുന്നു.",
        "pa": "AI ਨਤੀਜਿਆਂ ਦੀ ਵਿਆਖਿਆ:\n1. MobileNetV2 ਫਸਲ ਦੀ ਬਿਮਾਰੀ ਦੀ ਪਛਾਣ ਕਰਦਾ ਹੈ।\n2. ਦਿੱਖ ਨੁਕਸਾਨ ਅੰਦਾਜ਼ਾ ਫੋਟੋ ਤੋਂ ਨੁਕਸਾਨ ਦੀ % ਮਾਪਦਾ ਹੈ।\n3. ਮੌਸਮ ਜਾਂਚ ਮੀਂਹ ਅਤੇ ਤਾਪਮਾਨ ਦੀ ਪੁਸ਼ਟੀ ਕਰਦੀ ਹੈ।\n4. ਅੰਤਿਮ ਫੈਸਲਾ ਮਨੁੱਖੀ ਅਧਿਕਾਰੀ ਹੀ ਕਰਦਾ ਹੈ।",
        "as": "AI ফলাফলৰ ব্যাখ্যা:\n১. MobileNetV2 য়ে শস্যৰ ৰোগ চিনাক্ত কৰে।\n২. দৃশ্যমান ক্ষতি অনুমানে ফটোৰ পৰা ক্ষতিৰ % জুখে।\n৩. বতৰ পৰীক্ষণে বৃষ্টিপাত আৰু উষ্ণতা পৰীক্ষা কৰে।\n৪. মানৱ বিষয়াইহে চূড়ান্ত সিদ্ধান্ত লয়।",
        "or": "AI ଫଳାଫଳର ବ୍ୟାଖ୍ୟା:\n୧. MobileNetV2 ଫସଲ ରୋଗ ଚିହ୍ନଟ କରେ।\n୨. ଦୃଶ୍ୟ କ୍ଷତି ଅନୁମାନ ଫଟୋରୁ କ୍ଷତି % ମାପେ।\n୩. ପାଣିପାଗ ଯାଞ୍ଚ ବର୍ଷା ଓ ତାପମାତ୍ରା ନିଶ୍ଚିତ କରେ।\n୪. ମାନବ ଅଧିକାରୀ ହିଁ ଅନ୍ତିମ ନିଷ୍ପତ୍ତି ନିଅନ୍ତି।"
    },

    "REVIEW_STATUS": {
        "en": "Understanding Claim Review Statuses:\n• 🟢 NORMAL REVIEW: Routine processing. Claimed loss and AI visual/satellite signals are closely aligned. Standard verification.\n• 🟡 MEDIUM REVIEW: Additional verification advised. Minor discrepancies detected between claimed loss and photo evidence.\n• 🔴 HIGH REVIEW: High-priority inspection flagged. Significant divergence between farmer claim and AI/satellite indicators requiring detailed on-site field audit.\nNone of these statuses auto-approve or reject claims — an authorized human PMFBY officer conducts the review before any final payout.",
        "hi": "समीक्षा स्थिति श्रेणियों की जानकारी:\n• 🟢 NORMAL REVIEW: सामान्य नियमित प्रक्रिया। दावा किया गया नुकसान और AI/उपग्रह संकेत आपस में मेल खाते हैं।\n• 🟡 MEDIUM REVIEW: अतिरिक्त सत्यापन अनुशंसित। दावे और फोटो साक्ष्य में मामूली अंतर।\n• 🔴 HIGH REVIEW: उच्च प्राथमिकता वाली गहन जांच। दावे और AI संकेतों में बड़ा अंतर, जिसे अधिकारी द्वारा स्थलीय निरीक्षण की आवश्यकता है।\nइनमें से कोई भी स्थिति स्वचालित रूप से दावा स्वीकार या अस्वीकार नहीं करती; अधिकृत मानव अधिकारी ही अंतिम निर्णय लेते हैं।",
        "mr": "पुनरावलोकन स्थिती समजून घ्या:\n• 🟢 NORMAL REVIEW: नियमित प्रक्रिया. दावा केलेले नुकसान आणि AI पुरावे सुसंगत आहेत.\n• 🟡 MEDIUM REVIEW: अतिरिक्त पडताळणी आवश्यक. दावा आणि फोटोमध्ये किरकोळ तफावत आढळली आहे.\n• 🔴 HIGH REVIEW: उच्च प्राधान्याने सखोल तपासणी. दावा आणि उपग्रह/AI निष्कर्षांमध्ये लक्षणीय फरक असल्याने प्रत्यक्ष शेत तपासणी आवश्यक आहे.\nयापैकी कोणतीही स्थिती दावा आपोआप मंजूर किंवा नाकारत नाही; अधिकृत मानवी अधिकारीच अंतिम निर्णय घेतात.",
        "ta": "ஆய்வு நிலைகள்:\n• 🟢 NORMAL REVIEW: வழக்கமான செயல்முறை.\n• 🟡 MEDIUM REVIEW: கூடுதல் கள ஆய்வு தேவை.\n• 🔴 HIGH REVIEW: முன்னுரிமை தீவிர ஆய்வு தேவை.\nஇவை எவையும் தானாக முடிவெடுக்காது; மனித அதிகாரியே இறுதி முடிவெடுப்பார்.",
        "te": "సమీక్ష స్థితులు:\n• 🟢 NORMAL REVIEW: సాధారణ ప్రక్రియ.\n• 🟡 MEDIUM REVIEW: అదనపు క్షేత్ర స్థాయి తనిఖీ అవసరం.\n• 🔴 HIGH REVIEW: అధిక ప్రాధాన్యతతో కూడిన పరిశీలన అవసరం.\nతుది నిర్ణయాన్ని ఎల్లప్పుడూ మానవ అధికారే తీసుకుంటారు.",
        "bn": "পর্যালোচনা স্থিতি:\n• 🟢 NORMAL REVIEW: স্বাভাবিক প্রক্রিয়া।\n• 🟡 MEDIUM REVIEW: অতিরিক্ত যাচাইকরণ প্রয়োজন।\n• 🔴 HIGH REVIEW: উচ্চ অগ্রাধিকার পরিদর্শন প্রয়োজন।\nচূড়ান্ত সিদ্ধান্ত মানব কর্মকর্তা নেবেন।",
        "gu": "સમીક્ષા સ્થિતિ:\n• 🟢 NORMAL REVIEW: સામાન્ય પ્રક્રિયા.\n• 🟡 MEDIUM REVIEW: વધારાની ચકાસણી જરૂરી.\n• 🔴 HIGH REVIEW: ઉચ્ચ પ્રાથમિકતા તપાસ જરૂરી.\nઅંતિમ નિર્ણય હંમેશા માનવ અધિકારી લે છે.",
        "kn": "ಪರಿಶೀಲನಾ ಹಂತಗಳು:\n• 🟢 NORMAL REVIEW: ಸಾಮಾನ್ಯ ಪರಿಶೀಲನೆ.\n• 🟡 MEDIUM REVIEW: ಹೆಚ್ಚುವರಿ ಕ್ಷೇತ್ರ ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ.\n• 🔴 HIGH REVIEW: ಹೆಚ್ಚಿನ ಆದ್ಯತೆಯ ತಪಾಸಣೆ ಅಗತ್ಯವಿದೆ.\nಅಂತಿಮ ನಿರ್ಧಾರವನ್ನು ಮಾನವ ಅಧಿಕಾರಿಯೇ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ.",
        "ml": "അവലോകന നിലകൾ:\n• 🟢 NORMAL REVIEW: സാധാരണ പരിശോധന.\n• 🟡 MEDIUM REVIEW: കൂടുതൽ പരിശോധന ആവശ്യമാണ്.\n• 🔴 HIGH REVIEW: ഉയർന്ന മുൻഗണനയോടെയുള്ള പരിശോധന.\nമനുഷ്യ ഉദ്യോഗസ്ഥൻ മാത്രമാണ് അന്തിമ തീരുമാനമെടുക്കുന്നത്.",
        "pa": "ਸਮੀਖਿਆ ਸਥਿਤੀਆਂ:\n• 🟢 NORMAL REVIEW: ਆਮ ਪ੍ਰਕਿਰਿਆ।\n• 🟡 MEDIUM REVIEW: ਹੋਰ ਪੜਤਾਲ ਦੀ ਲੋੜ ਹੈ।\n• 🔴 HIGH REVIEW: ਉੱਚ ਤਰਜੀਹੀ ਜਾਂਚ ਦੀ ਲੋੜ ਹੈ।\nਅੰਤਿਮ ਫੈਸਲਾ ਮਨੁੱਖੀ ਅਧਿਕਾਰੀ ਹੀ ਕਰਦਾ ਹੈ।",
        "as": "পৰ্যালোচনা স্থিতি:\n• 🟢 NORMAL REVIEW: নিয়মীয়া প্ৰক্ৰিয়া।\n• 🟡 MEDIUM REVIEW: অতিৰিক্ত পৰীক্ষণৰ প্ৰয়োজন।\n• 🔴 HIGH REVIEW: অগ্ৰাধিকাৰমূলক পৰীক্ষণৰ প্ৰয়োজন।\nমানৱ বিষয়াইহে চূড়ান্ত সিদ্ধান্ত লয়।",
        "or": "ସମୀକ୍ଷା ସ୍ଥିତି:\n• 🟢 NORMAL REVIEW: ସାଧାରଣ ପ୍ରକ୍ରିୟା।\n• 🟡 MEDIUM REVIEW: ଅଧିକ ଯାଞ୍ଚ ଆବଶ୍ୟକ।\n• 🔴 HIGH REVIEW: ଉଚ୍ଚ ପ୍ରାଥମିକତା ଯାଞ୍ଚ ଆବଶ୍ୟକ।\nଅନ୍ତିମ ନିଷ୍ପତ୍ତି ମାନବ ଅଧିକାରୀ ହିଁ ନିଅନ୍ତି।"
    },

    "GREETING": {
        "en": "Hello! 👋 I am your PMFBY Project Assistant. I can help you use this website:\n• How to log in or register\n• How to submit a crop damage insurance claim\n• Where to view your claims and review status (Reports)\n• How to use the Dashboard, Satellite Analysis, and AI/ML Performance\nWhat would you like assistance with today?",
        "hi": "नमस्ते! 👋 मैं आपका PMFBY प्रोजेक्ट सहायक हूँ। मैं इस वेबसाइट का उपयोग करने में आपकी मदद कर सकता हूँ:\n• लॉगिन या पंजीकरण कैसे करें\n• फसल क्षति बीमा दावा कैसे जमा करें\n• अपने पिछले दावों की स्थिति कहाँ देखें (Reports)\n• डैशबोर्ड, उपग्रह विश्लेषण और AI/ML Performance का उपयोग कैसे करें\nआज मैं आपकी क्या सहायता कर सकता हूँ?",
        "mr": "नमस्कार! 👋 मी तुमचा PMFBY प्रकल्प सहाय्यक आहे. मी या वेबसाइटचा वापर करण्यासाठी मदत करू शकतो:\n• लॉगिन किंवा नोंदणी कशी करावी\n• पीक नुकसान विमा दावा कसा सादर करावा\n• तुमचे सादर केलेले दावे आणि स्थिती कुठे पाहावी (Reports)\n• डॅशबोर्ड, उपग्रह विश्लेषण आणि AI/ML Performance चा वापर कसा करावा\nआज मी तुम्हाला कशात मदत करू?",
        "ta": "வணக்கம்! 👋 நான் உங்கள் PMFBY திட்ட உதவியாளர். லாகின், பதிவு, காப்பீட்டு கோரிக்கை సమர்ப்பித்தல், செயற்கைக்கோள் பகுப்பாய்வு அல்லது கோரிக்கை நிலையை அறிய என்னிடம் கேட்கலாம்.",
        "te": "నమస్తే! 👋 నేను మీ PMFBY ప్రాజెక్ట్ సహాయకుడిని. లాగిన్, రిజిస్ట్రేషన్, బీమా క్లెయిమ్ సమర్పణ, ఉపగ్రహ విశ్లేషణ లేదా క్లెయిమ్ స్థితి గురించి నన్ను అడగవచ్చు.",
        "bn": "নমস্কার! 👋 আমি আপনার PMFBY প্রজেক্ট সহকারী। লগইন, নিবন্ধন, বিমা দাবি জমা, স্যাটেলাইট বিশ্লেষণ বা দাবির স্থিতি জানতে আমাকে জিজ্ঞাসা করতে পারেন।",
        "gu": "નમસ્તે! 👋 હું તમારો PMFBY પ્રોજેક્ટ સહાયક છું. લૉગિન, નોંધણી, વીમા દાવો સબમિટ કરવા, સેટેલાઇટ વિશ્લેષણ અથવા દાવાની સ્થિતિ વિશે પૂછી શકો છો.",
        "kn": "ನಮಸ್ಕಾರ! 👋 ನಾನು ನಿಮ್ಮ PMFBY ಪ್ರಾಜೆಕ್ಟ್ ಸಹಾಯಕ. ಲಾಗಿನ್, ನೋಂದಣಿ, ವಿಮಾ ಹಕ್ಕು ಸಲ್ಲಿಕೆ, ಉಪಗ್ರಹ ವಿಶ್ಲೇಷಣೆ ಅಥವಾ ಹಕ್ಕಿನ ಸ್ಥಿತಿಯ ಬಗ್ಗೆ ಕೇಳಬಹುದು.",
        "ml": "നമസ്കാരം! 👋 ഞാൻ നിങ്ങളുടെ PMFBY പ്രോജക്റ്റ് അസിസ്റ്റന്റാണ്. ലോഗിൻ, രജിസ്ട്രേഷൻ, ഇൻഷുറൻസ് ക്ലെയിം, ഉപഗ്രഹ വിശകലനം എന്നിവയെക്കുറിച്ച് ചോദിക്കാം.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! 👋 ਮੈਂ ਤੁਹਾਡਾ PMFBY ਪ੍ਰੋਜੈਕਟ ਸਹਾਇਕ ਹਾਂ। ਲੌਗਇਨ, ਰਜਿਸਟ੍ਰੇਸ਼ਨ, ਬੀਮਾ ਦਾਅਵਾ, ਸੈਟੇਲਾਈਟ ਵਿਸ਼ਲੇਸ਼ਣ ਜਾਂ ਦਾਅਵੇ ਦੀ ਸਥਿਤੀ ਬਾਰੇ ਪੁੱਛ ਸਕਦੇ ਹੋ।",
        "as": "নমস্কাৰ! 👋 মই আপোনাৰ PMFBY সহায়ক। লগইন, পঞ্জীয়ন, বীমা দাবী দাখিল, উপগ্ৰহ বিশ্লেষণ বা দাবীৰ স্থিতি সম্পৰ্কে সুধিব পাৰে।",
        "or": "ନମସ୍କାର! 👋 ମୁଁ ଆପଣଙ୍କର PMFBY ପ୍ରୋଜେକ୍ଟ ସହାୟକ। ଲଗଇନ, ପଞ୍ଜୀକରଣ, ବୀମା ଦାବି ଦାଖଲ, ଉପଗ୍ରହ ବିଶ୍ଳେଷଣ କିମ୍ବା ଦାବି ସ୍ଥିତି ବିଷୟରେ ପଚାରିପାରିବେ।"
    }
}

def classify_local_intent(message: str) -> Optional[str]:
    """
    Classifies user message into a high-confidence local intent.
    Supports English, Hindi, Marathi, and phonetic/transliterated variations.
    """
    msg = (message or "").strip().lower()
    if not msg:
        return None

    # 1. LOGOUT
    if re.search(r"\b(logout|log out|sign out|signout)\b", msg) or any(w in msg for w in ["लॉगआउट", "लॉग आउट", "साइन आउट", "बाहेर पडा"]):
        return "LOGOUT"

    # 2. FORGOT / RESET PASSWORD
    if re.search(r"\b(forgot|reset|recover)\b.*\b(password|token)\b|\b(password|token)\b.*\b(forgot|reset|recover)\b", msg) or \
       any(w in msg for w in ["password bhul", "password visarl", "पासवर्ड भूल", "पासवर्ड रीसेट", "पासवर्ड बदला", "पासवर्ड विसर", "கடவுச்சொல்", "పాస్‌వర్డ్", "পাসওয়ার্ড"]):
        return "FORGOT_PASSWORD"

    # 3. REGISTER / SIGN UP
    if re.search(r"\b(how to register|where to register|register kaise|create account|sign up|signup|new account|how to signup|register account|registration)\b", msg) or \
       any(w in msg for w in ["रजिस्टर", "पंजीकरण", "नोंदणी", "khata kaise banaye", "account kaise banaye", "nondani kashi", "பதிவு", "రిజిస్టర్", "নিবন্ধন", "નોંધણી", "ನೋಂದಣಿ"]):
        return "REGISTER"

    # 4. LOGIN / SIGN IN (Project-specific)
    if re.search(r"\b(how to log\s*in|how do i log\s*in|where is log\s*in|where can i log\s*in|how can i sign\s*in|how to sign\s*in|want to log\s*in|access my account|how to signin|login steps|login procedure)\b", msg) or \
       re.search(r"\b(login|log in|signin|sign in)\s+(kaise|kasa|kase|process|procedure|steps|option|button|page|link|help|kahan|kuthe|kaha)\b", msg) or \
       any(w in msg for w in ["login kaise", "login kasa", "login kase", "login kaha", "login kahan", "लॉगिन कैसे", "लॉग इन कैसे", "लॉगिन कहाँ", "लॉगिन कसा", "लॉगिन कुठे", "லாகின் எப்படி", "ఎలా లాగిన్", "কীভাবে লগইন"]):
        return "LOGIN"
    # Exact single word query "login", "sign in"
    if re.search(r"^(login|log in|sign in|signin)\??$", msg):
        return "LOGIN"

    # 5. SUBMIT CLAIM
    if re.search(r"\b(how to submit|how to apply|how do i claim|file a claim|submit a claim|submit claim|new claim|apply for claim|claim kaise|dava kaise|claim kasa|dava kasa|claim submission)\b", msg) or \
       any(w in msg for w in ["दावा कैसे", "दावा कसा", "दावा सादर", "नुकसान दावा", "कोரிக்கை சமர்ப்பிக்க", "క్లెయిమ్ సమర్పణ", "দাবি জমা"]):
        return "SUBMIT_CLAIM"

    # 6. WHERE TO SEE CLAIMS / CLAIM HISTORY / REPORTS
    if re.search(r"\b(where.*see.*claims?|where.*find.*claims?|where.*are.*claims?|claim history|past claims|previous claims|see my claims|check my claims|view claims|reports page|reports tab)\b", msg) or \
       any(w in msg for w in ["दावा इतिहास", "दाव्यांचा इतिहास", "पुराने दावे", "माझे दावे", "कहाँ देखें"]):
        return "CLAIM_HISTORY"

    # 7. CLAIM STATUS / CHECK STATUS
    if re.search(r"\b(claim status|track.*claim|status of.*claim|check.*status|review status)\b", msg) or \
       any(w in msg for w in ["दावा स्थिति", "दाव्याची स्थिती", "स्टेटस", "நிலை"]):
        return "CLAIM_STATUS"

    # 8. DASHBOARD
    if re.search(r"\b(what is.*dashboard|how to use.*dashboard|dashboard features?|where is.*dashboard|about dashboard)\b", msg) or \
       any(w in msg for w in ["डैशबोर्ड", "डॅशबोर्ड"]):
        return "DASHBOARD"

    # 9. PROFILE
    if re.search(r"\b(where is.*profile|how to.*profile|my profile|edit profile|view profile|profile page)\b", msg) or \
       any(w in msg for w in ["मेरी प्रोफाइल", "माझी प्रोफाइल", "प्रोफ़ाइल"]):
        return "PROFILE"

    # 10. ABOUT PROJECT / WEBSITE OVERVIEW
    if re.search(r"\b(what does this website do|what is this website|about this project|about pmfby website|how does this system work|website features|what is pmfby website)\b", msg) or \
       any(w in msg for w in ["वेबसाइट क्या करती है", "प्रकल्पाबद्दल माहिती", "प्रोजेक्ट क्या है"]):
        return "ABOUT_PROJECT"

    # 11. NDVI / SATELLITE ANALYSIS
    if re.search(r"\b(what is ndvi|ndvi|satellite analysis|sentinel|sentinel-2|earth engine|vegetation index)\b", msg) or \
       any(w in msg for w in ["उपग्रह विश्लेषण", "सॅटेलाइट"]):
        return "SATELLITE_NDVI"

    # 12. AI RESULT / MOBILENET / HEURISTIC
    if re.search(r"\b(explain.*ai result|ai result|disease prediction|mobilenet|heuristic estimate|visual estimate|difference between.*ai)\b", msg) or \
       any(w in msg for w in ["रोग पहचान", "दृश्य नुकसान"]):
        return "AI_RESULT"

    # 13. CLAIM RISK / REVIEW STATUS
    if re.search(r"\b(what does claim risk mean|claim risk|risk score|normal review|medium review|high review|review triage)\b", msg):
        return "REVIEW_STATUS"

    # 14. GREETINGS (Only if short query)
    if re.search(r"^(hi|hello|hey|hii|namaste|namaskar|vanakkam|pranam|good morning|good afternoon|good evening)[!.? ]*$", msg):
        return "GREETING"

    return None

def get_local_intent_response(intent: str, lang: str, user: Optional[Dict[str, Any]]) -> str:
    """
    Renders context-aware local response in the requested language.
    """
    l = lang if lang in SUPPORTED_LANGUAGES else "en"

    if intent == "LOGIN":
        if user:
            tmpl = LOCAL_RESPONSES["LOGIN_LOGGED_IN"].get(l, LOCAL_RESPONSES["LOGIN_LOGGED_IN"]["en"])
            return tmpl.format(
                name=user.get("name") or user.get("username", "Farmer"),
                username=user.get("username", "farmer"),
                district=user.get("district", "Your District"),
                state=user.get("state", "Your State")
            )
        return LOCAL_RESPONSES["LOGIN_LOGGED_OUT"].get(l, LOCAL_RESPONSES["LOGIN_LOGGED_OUT"]["en"])

    if intent == "LOGOUT":
        if user:
            return LOCAL_RESPONSES["LOGOUT_LOGGED_IN"].get(l, LOCAL_RESPONSES["LOGOUT_LOGGED_IN"]["en"])
        return LOCAL_RESPONSES["LOGOUT_LOGGED_OUT"].get(l, LOCAL_RESPONSES["LOGOUT_LOGGED_OUT"]["en"])

    if intent == "PROFILE":
        if user:
            tmpl = LOCAL_RESPONSES["PROFILE_LOGGED_IN"].get(l, LOCAL_RESPONSES["PROFILE_LOGGED_IN"]["en"])
            return tmpl.format(
                name=user.get("name") or user.get("username", "Farmer"),
                username=user.get("username", "farmer"),
                district=user.get("district", "Not set"),
                state=user.get("state", "Not set")
            )
        return LOCAL_RESPONSES["PROFILE_LOGGED_OUT"].get(l, LOCAL_RESPONSES["PROFILE_LOGGED_OUT"]["en"])

    if intent == "CLAIM_STATUS":
        if user:
            return get_user_claims_summary(user["id"], l)
        return LOCAL_RESPONSES["CLAIM_STATUS_LOGGED_OUT"].get(l, LOCAL_RESPONSES["CLAIM_STATUS_LOGGED_OUT"]["en"])

    if intent == "CLAIM_HISTORY":
        if user:
            summary = get_user_claims_summary(user["id"], l)
            hist_info = LOCAL_RESPONSES["CLAIM_HISTORY"].get(l, LOCAL_RESPONSES["CLAIM_HISTORY"]["en"])
            return f"{summary}\n\n{hist_info}"
        return LOCAL_RESPONSES["CLAIM_HISTORY"].get(l, LOCAL_RESPONSES["CLAIM_HISTORY"]["en"])

    if intent in LOCAL_RESPONSES:
        return LOCAL_RESPONSES[intent].get(l, LOCAL_RESPONSES[intent]["en"])

    return LOCAL_RESPONSES["GREETING"].get(l, LOCAL_RESPONSES["GREETING"]["en"])

# =========================================================
# FAST GEMINI API INTEGRATION (For Non-FAQ & General Queries)
# =========================================================

def call_gemini_api(
    api_key: str,
    message: str,
    language: str,
    user: Optional[Dict[str, Any]],
    context: Optional[dict],
) -> Optional[str]:
    """
    Calls Google Gemini API for general agriculture and contextual questions.
    Uses active, fast models (gemini-3-flash-preview, gemini-3.1-flash-lite-preview)
    with a strict 8-second timeout and guardrails against government portal hallucination.
    """
    lang_name = LANGUAGE_NAMES.get(language, "English")

    user_info = (
        f"Logged-in Farmer: {user.get('name', 'Farmer')}, "
        f"State: {user.get('state', '')}, "
        f"District: {user.get('district', '')}"
        if user
        else "User is not logged in (pre-login guest farmer)."
    )

    system_instruction = (
        f"You are a helpful AI assistant inside this specific PMFBY Crop Damage Detection & Claim Verification web application. "
        f"{user_info}. "
        f"Context: {json.dumps(context or {})}. "
        f"Answer exclusively in {lang_name}. "
        f"CRITICAL PROJECT RULES: "
        f"1. This is a standalone university/research project web application with its own UI: Dashboard, Damage Analysis, Study Area, Insurance Claim, Reports, AI/ML Performance, and Login/Register. "
        f"2. NEVER tell the user to visit pmfby.gov.in, use the official government PMFBY mobile app, go to Farmer Corner, or visit a CSC center. All website instructions must refer exclusively to this web application's UI. "
        f"3. Never approve or reject claims, never promise financial payouts, or calculate final compensation. "
        f"4. Give direct, polite, and practical agronomic, disease identification, and project assistance."
    )

    # Active, fast models verified with the API
    models_to_try = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
    ]

    for model_name in models_to_try:
        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model_name}:generateContent"
        )

        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"{system_instruction}\n\n"
                                f"Farmer Question: {message}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 600,
            },
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=8) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    text = part.get("text")
                    if text:
                        return text.strip()

        except urllib.error.HTTPError as e:
            # Temporary availability or rate-limit: try next model
            if e.code in (429, 500, 502, 503, 504):
                continue
            return None

        except Exception:
            continue

    return None

def get_contextual_fallback(message: str, language: str, user: Optional[Dict[str, Any]]) -> str:
    """
    Fallback if Gemini is offline or fails.
    """
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    intent = classify_local_intent(message)
    if intent:
        return get_local_intent_response(intent, lang, user)
    return LOCAL_RESPONSES["GREETING"].get(lang, LOCAL_RESPONSES["GREETING"]["en"])

def process_assistant_chat(
    message: str,
    language: str,
    authorization: Optional[str] = None,
    context: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Main processing entry point:
    1. FAST LOCAL INTENT ENGINE (<5ms): Immediately serves common project actions and FAQs without network delays.
    2. PRE-LOGIN PRIVATE DATA CHECK: Blocks unauthenticated access to personal financial/account details.
    3. GEMINI API: Invoked for general agricultural, disease diagnosis, or unclassified queries.
    4. FALLBACK ENGINE: Returns accurate local 12-language responses if Gemini is unavailable.
    """
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    user = get_optional_user_from_header(authorization)
    clean_msg = (message or "").strip()

    # 1. FAST LOCAL INTENT LAYER (ZERO DELAY):
    # If high-confidence project intent is detected, return immediately (<5ms)
    intent = classify_local_intent(clean_msg)
    if intent is not None:
        local_reply = get_local_intent_response(intent, lang, user)
        return {
            "reply": local_reply,
            "language": lang,
            "authenticated": user is not None,
            "source": "local_fast"
        }

    # 2. PRE-LOGIN PRIVATE DATA CHECK:
    # If user is not logged in and asks for personal private records (e.g. payout amount, personal account balance)
    if user is None and is_personal_query(clean_msg):
        return {
            "reply": LOGIN_REQUIRED_MESSAGES.get(lang, LOGIN_REQUIRED_MESSAGES["en"]),
            "language": lang,
            "authenticated": False,
            "source": "auth_guard"
        }

    # 3. GEMINI GENERATIVE CALL (for non-FAQ, general agronomy/farming inquiries):
    gemini_key = load_env_gemini_key()
    if gemini_key:
        reply = call_gemini_api(gemini_key, clean_msg, lang, user, context)
        if reply:
            return {
                "reply": reply,
                "language": lang,
                "authenticated": user is not None,
                "source": "gemini"
            }

    # 4. CONTEXTUAL 12-LANGUAGE FALLBACK:
    fallback_reply = get_contextual_fallback(clean_msg, lang, user)
    return {
        "reply": fallback_reply,
        "language": lang,
        "authenticated": user is not None,
        "source": "contextual_engine"
    }

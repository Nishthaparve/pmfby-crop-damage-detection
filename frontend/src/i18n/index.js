import en from "./en.json";
import hi from "./hi.json";
import mr from "./mr.json";
import ta from "./ta.json";
import te from "./te.json";
import bn from "./bn.json";
import gu from "./gu.json";
import kn from "./kn.json";
import ml from "./ml.json";
import pa from "./pa.json";
import assamese from "./as.json";
import odia from "./or.json";

export const languages = [
  ["en", "English"], ["hi", "हिन्दी"], ["mr", "मराठी"], ["ta", "தமிழ்"],
  ["te", "తెలుగు"], ["bn", "বাংলা"], ["gu", "ગુજરાતી"], ["kn", "ಕನ್ನಡ"],
  ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["as", "অসমীয়া"], ["or", "ଓଡ଼ିଆ"],
];

export const speechLocales = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
  ta: "ta-IN",
  te: "te-IN",
  bn: "bn-IN",
  gu: "gu-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  pa: "pa-IN",
  as: "as-IN",
  or: "or-IN"
};

const catalogs = {
  en, hi, mr, ta, te, bn, gu, kn, ml, pa, as: assamese, or: odia
};

const places = {
  mr: { Nagpur: "नागपूर", Maharashtra: "महाराष्ट्र" },
  hi: { Nagpur: "नागपुर", Maharashtra: "महाराष्ट्र" },
  ta: { Nagpur: "நாக்பூர்", Maharashtra: "மகாராஷ்டிரா" },
  te: { Nagpur: "నాగ్‌పూర్", Maharashtra: "మహారాష్ట్ర" },
  bn: { Nagpur: "নাগপুর", Maharashtra: "মহারাষ্ট্র" },
  gu: { Nagpur: "નાગપુર", Maharashtra: "મહારાષ્ટ્ર" },
  kn: { Nagpur: "ನಾಗ್ಪುರ", Maharashtra: "ಮಹಾರಾಷ್ಟ್ರ" },
  ml: { Nagpur: "നാഗ്പുർ", Maharashtra: "മഹാരാഷ്ട്ര" },
  pa: { Nagpur: "ਨਾਗਪੁਰ", Maharashtra: "ਮਹਾਰਾਸ਼ਟਰ" },
  as: { Nagpur: "নাগপুৰ", Maharashtra: "মহাৰাষ্ট্ৰ" },
  or: { Nagpur: "ନାଗପୁର", Maharashtra: "ମହାରାଷ୍ଟ୍ର" },
};

export function translate(language, key, values = {}) {
  if (key && key.startsWith("place.")) {
    const placeName = key.slice(6);
    return places[language]?.[placeName] ?? placeName;
  }
  let value = catalogs[language]?.[key] ?? catalogs.en?.[key] ?? key;
  if (typeof value === "string" && values) {
    Object.entries(values).forEach(([name, replacement]) => {
      value = value.replaceAll(`{{${name}}}`, replacement);
    });
  }
  return value;
}

export default translate;

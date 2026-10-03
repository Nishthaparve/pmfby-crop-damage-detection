import { useEffect, useRef, useState } from "react";
import { languages, speechLocales } from "./i18n";

const API_BASE = "http://127.0.0.1:8000";

function localReply(question, language, t) {
  const text = question.toLowerCase();
  const marathi = {
    greeting: "नमस्कार! मी PMFBY वेबसाइट वापरण्यास मदत करू शकतो. लॉगिन, दावा, विश्लेषण किंवा दावा इतिहासाबद्दल विचारा.",
    login: "लॉगिन करण्यासाठी डाव्या बाजूच्या ‘लॉगिन / नोंदणी’ वर जा. तुमचे वापरकर्तानाव आणि पासवर्ड भरा, नंतर ‘लॉगिन’ निवडा.",
    claim: "विमा दावा विभाग उघडा. पीक, नुकसानीची टक्केवारी, शेताचे ठिकाण आणि फोटो भरा, नंतर दावा सादर करा.",
    analysis: "अभ्यास क्षेत्रात राज्य, जिल्हा आणि दोन्ही कालावधी निवडा. त्यानंतर विश्लेषण बटण निवडा.",
    history: "विमा दावा इतिहासात तुमचे आधीचे दावे, त्यांची स्थिती आणि पुनरावलोकन प्राधान्य दिसते.",
  };
  const english = {
    greeting: "Hello! I can help you use the PMFBY website. Ask about login, submitting a claim, analysis, or claim history.",
    login: "To log in, open Login / Register from the sidebar, enter your username and password, then select Login.",
    claim: "Open Insurance Claim. Enter the crop, loss percentage, farm location, and a crop-damage image, then submit the claim.",
    analysis: "Open Study Area, choose the state, district, and both date periods, then select Analyze.",
    history: "Open Insurance Claim History to view earlier claims, their status, and review priority.",
  };
  const replies = language === "mr" ? marathi : english;
  if (/login|log in|sign in|लॉगिन/.test(text)) return replies.login;
  if (/claim|insurance|दावा/.test(text)) return replies.claim;
  if (/analysis|analy[sz]|satellite|study|विश्लेषण/.test(text)) return replies.analysis;
  if (/history|status|इतिहास/.test(text)) return replies.history;
  if (/hello|hi\b|help|नमस्कार|मदत/.test(text)) return replies.greeting;
  return t("generalHelp");
}

export default function Chatbot({ language, t, context }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const speechLocalesRef = useRef(speechLocales);
  const languageName = languages.find(([code]) => code === language)?.[1] || language;

  useEffect(() => () => {
    recognitionRef.current?.stop();
    window.speechSynthesis?.cancel();
  }, []);

  const speak = (text) => {
    if (!("speechSynthesis" in window)) return setError(t("voiceUnsupported"));
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLocalesRef.current[language] || "en-IN";
    window.speechSynthesis.speak(utterance);
  };

  const ask = async (question = message) => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setMessages((items) => [...items, { role: "user", text: trimmed }]);
    setMessage(""); setError("");
    try {
      const response = await fetch(`${API_BASE}/assistant/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, language, context }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.reply) throw new Error("assistant-unavailable");
      setMessages((items) => [...items, { role: "assistant", text: data.reply }]);
      speak(data.reply);
    } catch {
      // A backend restart or an older server without this endpoint must never
      // expose implementation text such as "Not Found" to a farmer. The
      // localized guidance is still useful and retains the active language.
      // Keep the conversation useful even when the optional local chat route
      // is temporarily unavailable. `generalHelp` is translated in every
      // supported locale, unlike a raw network/server failure.
      const fallback = localReply(trimmed, language, t);
      setMessages((items) => [...items, { role: "assistant", text: fallback }]);
      speak(fallback);
    }
  };

  const startListening = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return setError(t("speechUnavailable"));
    setError("");
    const recognition = new Recognition();
    recognition.lang = speechLocales[language] || "en-IN";
    recognition.interimResults = false; recognition.continuous = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event) => setError(event.error === "not-allowed" ? t("micDenied") : t("speechUnavailable"));
    recognition.onresult = (event) => { const transcript = event.results[0][0].transcript; setMessage(transcript); ask(transcript); };
    recognitionRef.current = recognition;
    recognition.start();
  };

  return <div className="pmfby-chatbot">
    {open && <section className="chat-window" aria-label={t("chatTitle")}>
      <header><div><strong>{t("chatTitle")}</strong><small>{t("assistantLanguage")}: {languageName}</small></div><button onClick={() => setOpen(false)} aria-label={t("close")}>×</button></header>
      <p className="chat-disclaimer">{t("generalHelp")}</p>
      <div className="chat-messages" aria-live="polite">
        {messages.length === 0 && <p className="chat-empty">{t("askAssistant")}</p>}
        {messages.map((item, index) => <div className={`chat-message ${item.role}`} key={`${item.role}-${index}`}><span>{item.role === "user" ? "👤" : "🤖"}</span><p>{item.text}</p>{item.role === "assistant" && <button onClick={() => speak(item.text)} aria-label={t("speakResponse")}>{t("speakResponse")}</button>}</div>)}
      </div>
      {error && <p className="chat-error">{error}</p>}
      <div className="chat-controls">
        <input aria-label={t("typeQuestion")} value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} placeholder={t("typeQuestion")} />
        <button onClick={() => ask()} aria-label={t("send")}>{t("send")}</button>
        <button onClick={listening ? () => recognitionRef.current?.stop() : startListening} aria-label={listening ? t("stopListening") : t("startListening")}>{listening ? t("stopListening") : `🎤 ${t("startListening")}`}</button>
        <button onClick={() => window.speechSynthesis?.cancel()} aria-label={t("stopSpeaking")}>{t("stopSpeaking")}</button>
      </div>
    </section>}
    <button className="chat-fab" onClick={() => setOpen((value) => !value)} aria-label={t("askAssistant")}>💬 {t("askAssistant")}</button>
  </div>;
}

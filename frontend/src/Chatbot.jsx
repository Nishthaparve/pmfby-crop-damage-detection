import { useEffect, useRef, useState } from "react";
import { languages, speechLocales } from "./i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function Chatbot({ language, t, context, authUser, token }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const languageName = languages.find(([code]) => code === language)?.[1] || language;

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
      window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setSpeakingIndex(null);
  };

  const readAloud = (text, index) => {
    if (!("speechSynthesis" in window)) {
      return setError(t("voiceUnsupported"));
    }
    if (speakingIndex === index) {
      stopSpeaking();
      return;
    }
    stopSpeaking();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLocales[language] || "en-IN";
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);
    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  const ask = async (question = message) => {
    if (loading) return;
    const trimmed = question.trim();
    if (!trimmed) return;
    setMessages((items) => [...items, { role: "user", text: trimmed }]);
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/assistant/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: trimmed,
          language,
          context: {
            ...context,
            page: context?.page || "dashboard",
            authenticated: !!authUser,
            farmerName: authUser?.name,
            state: authUser?.state || context?.state,
            district: authUser?.district || context?.district
          }
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.reply) throw new Error("assistant-unavailable");
      // Response appears as text without automatic speech reading
      setMessages((items) => [...items, { role: "assistant", text: data.reply }]);
    } catch {
      // Local fallback in case backend is offline
      const fallback = t("generalHelp");
      setMessages((items) => [...items, { role: "assistant", text: fallback }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleListening = () => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return setError(t("speechUnavailable"));
    setError("");

    const recognition = new Recognition();
    recognition.lang = speechLocales[language] || "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event) => {
      setListening(false);
      setError(event.error === "not-allowed" ? t("micDenied") : t("speechUnavailable"));
    };
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (transcript) {
        setMessage(transcript);
        ask(transcript);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

// ---- Clean Line SVG Icons for Chatbot ----
function MessageSquareIcon({ size = 16, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function MicIcon({ size = 13, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

function SquareIcon({ size = 11, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" stroke="none" className={className}>
      <rect x="5" y="5" width="14" height="14" rx="2" />
    </svg>
  );
}

function VolumeIcon({ size = 12, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

function UserAvatarIcon({ size = 13, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function BotAvatarIcon({ size = 13, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect width="18" height="14" x="3" y="6" rx="2" />
      <circle cx="9" cy="13" r="1.5" fill="currentColor" />
      <circle cx="15" cy="13" r="1.5" fill="currentColor" />
      <path d="M12 2v4" />
    </svg>
  );
}

function LoaderIcon({ size = 12, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <line x1="12" x2="12" y1="2" y2="6" />
      <line x1="12" x2="12" y1="18" y2="22" />
      <line x1="4.93" x2="7.76" y1="4.93" y2="7.76" />
      <line x1="16.24" x2="19.07" y1="16.24" y2="19.07" />
      <line x1="2" x2="6" y1="12" y2="12" />
      <line x1="18" x2="22" y1="12" y2="12" />
      <line x1="4.93" x2="7.76" y1="19.07" y2="16.24" />
      <line x1="16.24" x2="19.07" y1="7.76" y2="4.93" />
    </svg>
  );
}

  return (
    <div className="pmfby-chatbot">
      {open && (
        <section className="chat-window" aria-label={t("chatTitle")}>
          <header>
            <div>
              <strong>{t("chatTitle")}</strong>
              <small>{t("assistantLanguage")}: {languageName}</small>
            </div>
            <button onClick={() => { setOpen(false); stopSpeaking(); }} aria-label={t("close")}>×</button>
          </header>
          <p className="chat-disclaimer">{t("generalHelp")}</p>
          <div className="chat-messages" aria-live="polite">
            {messages.length === 0 && <p className="chat-empty">{t("askAssistant")}</p>}
            {messages.map((item, index) => (
              <div className={`chat-message ${item.role}`} key={`${item.role}-${index}`}>
                <span className="chat-avatar" aria-hidden="true">
                  {item.role === "user" ? <UserAvatarIcon size={13} /> : <BotAvatarIcon size={13} />}
                </span>
                <p>{item.text}</p>
                {item.role === "assistant" && (
                  <button
                    type="button"
                    className={`chat-speak-btn ${speakingIndex === index ? "speaking" : ""}`}
                    onClick={() => readAloud(item.text, index)}
                    aria-label={speakingIndex === index ? t("stopSpeaking") : t("readAloud")}
                  >
                    {speakingIndex === index ? (
                      <>
                        <SquareIcon size={11} /> {t("stopSpeaking")}
                      </>
                    ) : (
                      <>
                        <VolumeIcon size={12} /> {t("readAloud")}
                      </>
                    )}
                  </button>
                )}
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant thinking">
                <span className="chat-avatar" aria-hidden="true">
                  <BotAvatarIcon size={13} />
                </span>
                <p className="chat-thinking-bubble">
                  <LoaderIcon size={12} className="spin-inline" /> {t("loading") || "Thinking..."}
                </p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {error && <p className="chat-error">{error}</p>}
          <div className="chat-controls">
            <input
              aria-label={t("typeQuestion")}
              value={message}
              disabled={loading}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && ask()}
              placeholder={loading ? (t("loading") || "Thinking...") : t("typeQuestion")}
            />
            <button
              type="button"
              disabled={loading || !message.trim()}
              onClick={() => ask()}
              aria-label={t("send")}
            >
              {loading ? "..." : t("send")}
            </button>
            <button
              type="button"
              disabled={loading}
              className={`chat-mic-btn ${listening ? "listening" : ""}`}
              onClick={toggleListening}
              aria-label={listening ? t("stopListening") : t("startListening")}
            >
              {listening ? (
                <>
                  <SquareIcon size={11} /> {t("stopListening")}
                </>
              ) : (
                <>
                  <MicIcon size={13} /> {t("startListening")}
                </>
              )}
            </button>
            {speakingIndex !== null && (
              <button
                type="button"
                className="chat-stop-all"
                onClick={stopSpeaking}
                aria-label={t("stopSpeaking")}
              >
                <SquareIcon size={11} /> {t("stopSpeaking")}
              </button>
            )}
          </div>
        </section>
      )}
      <button
        className="chat-fab"
        onClick={() => setOpen((value) => !value)}
        aria-label={t("askAssistant")}
      >
        <MessageSquareIcon size={16} />
        <span>{t("askAssistant")}</span>
      </button>
    </div>
  );
}

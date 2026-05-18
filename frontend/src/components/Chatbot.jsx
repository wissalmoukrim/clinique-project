import { useEffect, useRef, useState } from "react";
import { publicFetch } from "../api/client";

const MAX_MESSAGE_LENGTH = 480;

function createMessage(sender, text) {
  return {
    id: `${sender}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    sender,
    text,
    createdAt: new Date().toISOString(),
  };
}

function sanitizeOutgoingMessage(value) {
  return String(value || "")
    .replace(/<[^>]*>/g, "")
    .replace(/javascript:/gi, "")
    .replace(/\bon\w+\s*=/gi, "")
    .trim()
    .slice(0, MAX_MESSAGE_LENGTH);
}

function formatMessageTime(value) {
  return new Intl.DateTimeFormat("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function Chatbot() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    createMessage(
      "bot",
      "Bonjour. Je suis l'assistant public de la Clinique Medicale Elite. Je peux vous informer sur les specialites, les medecins, les horaires, le contact et la prise de rendez-vous."
    ),
  ]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, loading, open]);

  const sendMessage = async () => {
    const safeMessage = sanitizeOutgoingMessage(message);
    if (!safeMessage || loading) return;

    setMessages((prev) => [...prev, createMessage("user", safeMessage)]);
    setMessage("");
    setLoading(true);

    try {
      const data = await publicFetch("/chatbot/public/ask/", {
        method: "POST",
        body: { message: safeMessage },
      });

      setMessages((prev) => [
        ...prev,
        createMessage("bot", data.response || "Je peux repondre uniquement aux informations publiques de la clinique."),
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        createMessage("bot", error.message || "Impossible de contacter l'assistant pour le moment."),
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        className={`chat-toggle${open ? " is-open" : ""}`}
        type="button"
        onClick={() => setOpen(!open)}
        aria-label={open ? "Fermer l'assistant public" : "Ouvrir l'assistant public"}
        aria-expanded={open}
      >
        {open ? "x" : "Chat"}
      </button>

      <section className={`chatbot-container${open ? " is-open" : ""}`} aria-hidden={!open}>
          <div className="chatbot-header">
            <div className="chatbot-header-left">
              <div className="bot-avatar" aria-hidden="true">CE</div>
              <div>
                <h3>Assistant clinique</h3>
                <span><i aria-hidden="true" />{loading ? "Reponse en cours" : "En ligne"}</span>
              </div>
            </div>

            <button className="close-btn" type="button" onClick={() => setOpen(false)} aria-label="Fermer le chatbot">
              x
            </button>
          </div>

          <div className="chatbot-messages" role="log" aria-live="polite">
            {messages.map((msg) => (
              <article key={msg.id} className={msg.sender === "user" ? "message user" : "message bot"}>
                <p>{msg.text}</p>
                <time dateTime={msg.createdAt}>{formatMessageTime(msg.createdAt)}</time>
              </article>
            ))}
            {loading && (
              <article className="message bot typing" aria-label="L'assistant prepare une reponse">
                <span />
                <span />
                <span />
              </article>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form
            className="chatbot-input"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <input
              type="text"
              placeholder="Posez une question publique..."
              value={message}
              disabled={loading}
              maxLength={MAX_MESSAGE_LENGTH}
              onChange={(e) => setMessage(e.target.value)}
            />

            <button type="submit" disabled={loading || !sanitizeOutgoingMessage(message)}>
              {loading ? "..." : "Envoyer"}
            </button>
          </form>
      </section>
    </>
  );
}

export default Chatbot;

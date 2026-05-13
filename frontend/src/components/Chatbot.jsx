import { useState } from "react";
import { apiFetch } from "../api/client";

function Chatbot() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Bonjour. Je suis l'assistant patient de la Clinique Medicale Elite. Je peux vous aider avec vos questions de sante, vos rendez-vous et votre suivi.",
    },
  ]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || loading) return;

    setMessages((prev) => [...prev, { sender: "user", text: trimmedMessage }]);
    setMessage("");
    setLoading(true);

    try {
      const data = await apiFetch("/chatbot/ask/", {
        method: "POST",
        body: { message: trimmedMessage.slice(0, 500) },
      });

      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.response || "Je n'ai pas pu generer une reponse." },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: error.message || "Impossible de contacter l'assistant pour le moment." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        className="chat-toggle"
        type="button"
        onClick={() => setOpen(!open)}
        aria-label="Ouvrir l'assistant patient"
      >
        Chat
      </button>

      {open && (
        <div className="chatbot-container">
          <div className="chatbot-header">
            <div className="chatbot-header-left">
              <div className="bot-avatar">AI</div>
              <div>
                <h3>Assistant patient</h3>
                <span>{loading ? "Reponse..." : "En ligne"}</span>
              </div>
            </div>

            <button className="close-btn" type="button" onClick={() => setOpen(false)}>
              x
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, index) => (
              <div key={index} className={msg.sender === "user" ? "message user" : "message bot"}>
                {msg.text}
              </div>
            ))}
          </div>

          <div className="chatbot-input">
            <input
              type="text"
              placeholder="Ecrivez un message..."
              value={message}
              disabled={loading}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendMessage();
                }
              }}
            />

            <button type="button" onClick={sendMessage} disabled={loading || !message.trim()}>
              {loading ? "..." : "Envoyer"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbot;

import { useState } from "react";

function Chatbot() {

    const [message, setMessage] = useState("");

    const [messages, setMessages] = useState([
        {
            sender: "bot",
            text: "Bonjour 👋 Je suis le chatbot de la Clinique Médicale Elite. Je suis là pour répondre à vos questions concernant la clinique."
        }
    ]);

    const [open, setOpen] = useState(false);

    const sendMessage = async () => {

        if (!message.trim()) return;

        const userMessage = {
            sender: "user",
            text: message
        };

        setMessages((prev) => [...prev, userMessage]);

        try {

            const res = await fetch("http://127.0.0.1:8000/api/chatbot/ask/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: message
                })
            });

            const data = await res.json();

            const botMessage = {
                sender: "bot",
                text: data.response
            };

            setMessages((prev) => [...prev, botMessage]);

        } catch (error) {

            setMessages((prev) => [
                ...prev,
                {
                    sender: "bot",
                    text: "Erreur serveur"
                }
            ]);
        }

        setMessage("");
    };

    return (
        <>

            <button
                className="chat-toggle"
                onClick={() => setOpen(!open)}
            >
                💬
            </button>

            {open && (

                <div className="chatbot-container">

                    <div className="chatbot-header">

                        <div className="chatbot-header-left">

                            <div className="bot-avatar">
                                🤖
                            </div>

                            <div>
                                <h3>Chatbot Clinique</h3>
                                <span>En ligne</span>
                            </div>

                        </div>

                        <button
                            className="close-btn"
                            onClick={() => setOpen(false)}
                        >
                            ✕
                        </button>

                    </div>

                    <div className="chatbot-messages">

                        {messages.map((msg, index) => (

                            <div
                                key={index}
                                className={
                                    msg.sender === "user"
                                        ? "message user"
                                        : "message bot"
                                }
                            >
                                {msg.text}
                            </div>

                        ))}

                    </div>

                    <div className="chatbot-input">

                        <input
                            type="text"
                            placeholder="Écrivez un message..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    sendMessage();
                                }
                            }}
                        />

                        <button onClick={sendMessage}>
                            Envoyer
                        </button>

                    </div>

                </div>

            )}

        </>
    );
}

export default Chatbot;

     
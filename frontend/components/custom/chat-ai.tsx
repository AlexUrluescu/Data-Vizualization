"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User, AlertCircle } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWithAIProps {
  data?: any;
  dataDescription?: string;
}

export default function ChatWithAI({}: ChatWithAIProps) {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length === 0) return;

    const timeoutId = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }, 150);

    return () => clearTimeout(timeoutId);
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setError(null);

    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      // Folosește proxy-ul din next.config.js sau direct localhost
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";
      const API_URL =
        process.env.NODE_ENV === "production"
          ? "/api/traffic/ask"
          : `${apiUrl}/api/v1/traffic-chat-bot/ask`;

      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: userMessage }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${response.status}`);
      }

      const result = await response.json();

      const aiResponse = result.answer || "Nu am primit răspuns de la AI.";

      setMessages([...newMessages, { role: "assistant", content: aiResponse }]);
    } catch (err: any) {
      console.error("Eroare API trafic:", err);
      const msg = err.message.includes("Failed to fetch")
        ? "Nu pot contacta serverul Flask. Pornește `python app.py`"
        : err.message.includes("CORS")
        ? "Probleme CORS – folosește proxy în next.config.js"
        : err.message || "Eroare necunoscută";

      setError(msg);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Eroare: ${msg}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div
      style={{ marginTop: "-150px" }}
      className="bg-white rounded-lg shadow-2xl overflow-hidden border border-gray-200"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-5">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <Bot className="w-8 h-8" />
          UrbanBike Traffic AI
        </h2>
        <p className="text-sm opacity-90 mt-1">
          Întreabă despre traficul pe Bulevardul Corneliu Coposu
        </p>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-5 space-y-5 bg-gradient-to-b from-gray-50 to-white"
        style={{ minHeight: "500px", maxHeight: "650px" }}
      >
        {messages.length === 0 && (
          <div className="text-center mt-10">
            <Bot className="w-20 h-20 mx-auto mb-6 text-gray-300" />
            <p className="text-xl font-semibold text-gray-700">
              Bună! Sunt asistentul tău de trafic
            </p>
            <p className="text-gray-600 mt-2">
              Întreabă-mă orice despre trafic:
            </p>
            <div className="mt-6 space-y-3 max-w-2xl mx-auto text-left">
              {[
                "câte mașini au trecut azi?",
                "la ce oră a fost cel mai aglomerat?",
                "diferența între azi și ieri",
              ].map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setInput(ex)}
                  className="block w-full text-left bg-white p-4 rounded-xl shadow-sm border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all"
                >
                  <p className="text-sm font-medium text-gray-800">{ex}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.role === "assistant" && (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0 shadow-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
            )}
            <div
              className={`max-w-2xl px-5 py-4 rounded-2xl shadow-md ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-800 border border-gray-200"
              }`}
            >
              <p
                className="text-sm whitespace-pre-wrap font-medium leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: msg.content
                    .replace(
                      /\*\*(.*?)\*\*/g,
                      '<strong class="font-bold text-inherit">$1</strong>'
                    )
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
            {msg.role === "user" && (
              <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 shadow-lg">
                <User className="w-6 h-6 text-white" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="bg-white px-5 py-4 rounded-2xl shadow-md border border-gray-200">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          </div>
        )}

        {error && (
          <div className="flex gap-3 justify-start">
            <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <div className="bg-red-50 text-red-700 px-5 py-4 rounded-2xl border border-red-200">
              <p className="text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-5 bg-gray-50 border-t border-gray-200">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question ..."
            disabled={loading}
            className="flex-1 px-5 py-4 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 text-gray-800 font-medium"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-3 font-bold shadow-lg"
          >
            {loading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <>
                <Send className="w-6 h-6" />
                Trimite
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

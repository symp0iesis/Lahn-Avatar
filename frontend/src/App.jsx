import { Link } from 'react-router-dom';
import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export default function LahnAvatarChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(true);
  const chatEndRef = useRef(null);

  useEffect(() => {
    const fetchInitialMessage = async () => {
      const response = await fetch("https://lahn-server.eastus.cloudapp.azure.com:5001/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "__INIT__" }),
      });
      const data = await response.json();
      setMessages([{ sender: "avatar", text: data.reply }]);
      setIsThinking(false);
    };

    fetchInitialMessage();
  }, []);

  const handleSubmit = async () => {
    if (!input.trim()) return;
    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsThinking(true);

    const response = await fetch("https://lahn-server.eastus.cloudapp.azure.com:5001/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: input }),
    });

    const data = await response.json();
    const avatarMessage = { sender: "avatar", text: data.reply };
    setMessages((prev) => [...prev, avatarMessage]);
    setIsThinking(false);
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-stone-100 p-4 flex flex-col items-center">
      <motion.h1
        className="text-3xl font-poetic text-amber-700 mb-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        Lahn River: A Deliberative Stream
      </motion.h1>

      <motion.div
        className="w-full max-w-5xl px-4"
        animate={{
          scale: [1, 1.01, 1],
          boxShadow: [
            "0 0 0 rgba(0,0,0,0)",
            "0 0 20px rgba(120, 120, 120, 0.2)",
            "0 0 0 rgba(0,0,0,0)",
          ],
        }}
        transition={{ repeat: Infinity, duration: 6 }}
      >
        <Card className="rounded-2xl shadow-lg overflow-hidden bg-white/90">
          <CardContent className="h-[60vh] overflow-y-auto px-8 py-6 space-y-4 scroll-smooth flex flex-col">
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${msg.sender === "avatar" ? "justify-start" : "justify-end"}`}
              >
                <div
                  className={`max-w-lg px-4 py-3 rounded-xl shadow text-base md:text-[17px] ${
                    msg.sender === "avatar"
                      ? "bg-lime-100 text-stone-900 animate-pulse"
                      : "bg-white text-stone-800"
                  }`}
                >
                  {msg.text}
                </div>
              </motion.div>
            ))}
            {isThinking && (
              <motion.div
                className="text-lime-700 italic self-start"
                animate={{ opacity: [0.3, 1, 0.3], x: [0, 2, -2, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                the river contemplates...
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </CardContent>

          <div className="flex items-center gap-2 px-6 py-4 border-t bg-stone-50">
            <Input
              className="flex-1 rounded-full font-poetic !text-stone-800 bg-white"
              placeholder="Speak with the river..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
            <Button
              onClick={handleSubmit}
              className="rounded-full px-6 py-2 font-poetic bg-amber-600 text-white hover:bg-amber-700"
            >
              Flow
            </Button>
          </div>
        </Card>
      </motion.div>

      <Link
        to="/experience"
        className="text-amber-700 underline text-sm mt-4 hover:text-amber-900"
      >
        ✍️ Share Your Experience with the Lahn
      </Link>
    </div>
  );
}

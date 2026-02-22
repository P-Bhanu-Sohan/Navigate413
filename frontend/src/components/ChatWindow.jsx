import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, Languages } from 'lucide-react';

export function ChatWindow({ sessionId }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: 'Hi there. I can help you understand your documents. Upload one or ask me questions about financial aid, housing, or visa requirements.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
          language: selectedLanguage
        })
      });

      if (!response.ok) throw new Error('Chat request failed');
      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: data.response
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: `Error: ${err.message}. Please try again.`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-crimson-600 to-coral-500 text-white px-6 py-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Support Assistant</h3>
            <p className="text-xs text-slate-200 mt-1">Ask questions about your documents</p>
          </div>
          <div className="flex items-center gap-2">
            <Languages className="w-4 h-4" />
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-white text-slate-800 font-medium border border-white text-xs rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-white shadow-sm"
            >
              <option value="English" className="bg-slate-800">English</option>
              <option value="Spanish" className="bg-slate-800">Spanish</option>
              <option value="French" className="bg-slate-800">French</option>
              <option value="Chinese" className="bg-slate-800">Chinese</option>
              <option value="Hindi" className="bg-slate-800">Hindi</option>
              <option value="Arabic" className="bg-slate-800">Arabic</option>
            </select>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-slate-800 to-slate-850">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
          >
            <div
              className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm shadow-md ${
                message.type === 'user'
                  ? 'bg-gradient-to-br from-crimson-600 to-crimson-700 text-white rounded-br-sm'
                  : 'bg-slate-700/80 text-slate-100 rounded-bl-sm border border-slate-600/50'
              }`}
            >
              <p className="leading-relaxed" dangerouslySetInnerHTML={{ __html: message.text }}></p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-slate-700/80 text-slate-100 px-4 py-3 rounded-2xl rounded-bl-sm border border-slate-600/50 shadow-md">
              <div className="flex items-center gap-2">
                <Loader className="w-4 h-4 animate-spin text-crimson-400" />
                <span className="text-xs text-slate-400">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-700 p-4 bg-slate-800/95 backdrop-blur">
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-3 bg-slate-700/80 border border-slate-600 text-white placeholder-slate-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-crimson-500 focus:border-transparent transition-all text-sm hover:bg-slate-700"
            disabled={loading}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-gradient-to-r from-crimson-600 to-coral-600 hover:from-crimson-500 hover:to-coral-500 disabled:from-slate-600 disabled:to-slate-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 text-sm shadow-lg hover:shadow-crimson-500/25 hover:scale-105 active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-slate-400">Press Enter to send</p>
      </div>
    </div>
  );
}

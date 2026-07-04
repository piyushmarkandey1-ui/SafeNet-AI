import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send } from 'lucide-react';
import { GlassPanel } from '../ui';
import { askCitizenShield } from '../../lib/api';
import './CitizenShieldChat.css';

export function CitizenShieldChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    const botResponse = await askCitizenShield(input);
    
    setIsTyping(false);
    setMessages(prev => [...prev, botResponse]);
  };

  return (
    <div className="chat-widget">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="chat-window-wrapper"
          >
            <GlassPanel hoverable={false} className="chat-window">
              <div className="chat-header">
                <div>
                  <h3 className="chat-title">Citizen Shield AI</h3>
                  <span className="chat-status"><span className="status-dot healthy"/> Online</span>
                </div>
                <button className="icon-btn" onClick={() => setIsOpen(false)}>
                  <X size={18} />
                </button>
              </div>

              <div className="chat-messages" ref={scrollRef}>
                {messages.length === 0 && (
                  <p className="chat-empty">How can I assist you with fraud prevention today?</p>
                )}
                
                {messages.map((msg) => (
                  <motion.div 
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`chat-bubble-wrapper ${msg.sender === 'user' ? 'is-user' : 'is-bot'}`}
                  >
                    <div className={`chat-bubble ${msg.isActionable ? 'is-actionable' : ''}`}>
                      {msg.text}
                    </div>
                    <span className="chat-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </motion.div>
                ))}

                {isTyping && (
                  <motion.div 
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }} 
                    className="chat-typing"
                  >
                    <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                  </motion.div>
                )}
              </div>

              <form className="chat-input-area" onSubmit={handleSend}>
                <input
                  type="text"
                  placeholder="Ask about a suspicious call..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="chat-input"
                />
                <button type="submit" className="chat-send-btn" disabled={!input.trim() || isTyping}>
                  <Send size={16} />
                </button>
              </form>
            </GlassPanel>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        className={`chat-toggle ${isOpen ? 'is-open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <MessageSquare size={24} />
      </motion.button>
    </div>
  );
}

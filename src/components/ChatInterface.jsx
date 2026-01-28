import React, { useState, useEffect, useCallback, useRef } from 'react';
import { COLORS } from './constants';

/**
 * ChatInterface Component
 * Handles AI chat functionality with Smart Router integration
 * 
 * Refactored from App.jsx as part of P1 codebase improvements
 * @author BidDeed.AI / Everest Capital USA
 */

// Message bubble component
const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  
  const bubbleStyle = {
    maxWidth: '85%',
    padding: '12px 16px',
    borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
    backgroundColor: isUser ? COLORS.accent : COLORS.surface,
    color: isUser ? 'white' : COLORS.textPrimary,
    alignSelf: isUser ? 'flex-end' : 'flex-start',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  };

  const metaStyle = {
    fontSize: '11px',
    color: isUser ? 'rgba(255,255,255,0.7)' : COLORS.textSecondary,
    marginTop: '6px',
    display: 'flex',
    justifyContent: 'space-between',
  };

  return (
    <div style={bubbleStyle}>
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
        {message.content}
      </div>
      <div style={metaStyle}>
        <span>{message.timestamp?.toLocaleTimeString()}</span>
        {message.metadata?.tier && (
          <span style={{ 
            marginLeft: '8px', 
            padding: '2px 6px', 
            borderRadius: '4px',
            backgroundColor: message.metadata.tier === 'FREE' ? '#10B98120' : '#3B82F620',
            color: message.metadata.tier === 'FREE' ? '#10B981' : '#3B82F6',
            fontSize: '10px',
          }}>
            {message.metadata.tier}
          </span>
        )}
      </div>
    </div>
  );
};

// Typing indicator
const TypingIndicator = () => (
  <div style={{
    display: 'flex',
    gap: '4px',
    padding: '12px 16px',
    backgroundColor: COLORS.surface,
    borderRadius: '16px',
    width: 'fit-content',
  }}>
    {[0, 1, 2].map(i => (
      <div
        key={i}
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: COLORS.textSecondary,
          animation: `typing 1s infinite ${i * 0.2}s`,
        }}
      />
    ))}
    <style>{`
      @keyframes typing {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1); }
      }
    `}</style>
  </div>
);

// API Status Badge
const ApiStatusBadge = ({ status }) => {
  const statusConfig = {
    connected: { color: '#10B981', label: '● Connected' },
    error: { color: '#EF4444', label: '● Disconnected' },
    unknown: { color: '#F59E0B', label: '● Checking...' },
  };

  const config = statusConfig[status] || statusConfig.unknown;

  return (
    <span style={{
      fontSize: '11px',
      color: config.color,
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
    }}>
      {config.label}
    </span>
  );
};

/**
 * Main ChatInterface component
 */
export default function ChatInterface({ 
  siteContext,
  onSiteParamsExtracted,
  onResultsGenerated,
  apiBase = '',
}) {
  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: `Hi! I'm SPD.AI, your site planning assistant powered by Smart Router V7.4.\n\nI can help you with:\n• Feasibility analysis for 8 development types\n• Zoning requirements lookup\n• Pro forma calculations\n• Site comparison and recommendations\n\nTell me about your site - for example:\n• "I have 5 acres in Titusville, zoned C-2"\n• "What can I build on 10 acres with R-3 zoning?"\n• "Compare self-storage vs industrial for my 8-acre site"`,
      timestamp: new Date(),
      metadata: { tier: 'SYSTEM', model: 'welcome' }
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [apiStatus, setApiStatus] = useState('unknown');
  const [conversationHistory, setConversationHistory] = useState([]);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const res = await fetch(`${apiBase}/api/chat/health`);
      setApiStatus(res.ok ? 'connected' : 'error');
    } catch {
      setApiStatus('error');
    }
  };

  // Send message to API
  const sendToAPI = useCallback(async (message) => {
    try {
      const response = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          messages: conversationHistory,
          siteContext,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API call failed:', error);
      return {
        response: `I'm having trouble connecting to the AI service. Please try again.\n\n_Error: ${error.message}_`,
        metadata: { tier: 'ERROR', error: error.message },
      };
    }
  }, [conversationHistory, siteContext, apiBase]);

  // Extract site parameters from conversation
  const extractSiteParams = useCallback((userInput, response) => {
    const input = userInput.toLowerCase();
    
    // Extract acreage
    const acreageMatch = input.match(/(\d+(?:\.\d+)?)\s*(?:acres?|ac)/i);
    if (acreageMatch && onSiteParamsExtracted) {
      onSiteParamsExtracted({ acreage: parseFloat(acreageMatch[1]) });
    }
    
    // Extract zoning
    const zoningMatch = input.match(/(?:zoned?|zoning)\s*([A-Z]-?\d+|PUD)/i);
    if (zoningMatch && onSiteParamsExtracted) {
      onSiteParamsExtracted({ zoning: zoningMatch[1].toUpperCase() });
    }
  }, [onSiteParamsExtracted]);

  // Handle chat submit
  const handleChatSubmit = useCallback(async () => {
    if (!chatInput.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setConversationHistory(prev => [...prev, { role: 'user', content: chatInput.trim() }]);
    setChatInput('');
    setIsTyping(true);

    const apiResponse = await sendToAPI(chatInput.trim());

    const assistantMessage = {
      id: messages.length + 2,
      role: 'assistant',
      content: apiResponse.response,
      timestamp: new Date(),
      metadata: apiResponse.metadata,
    };

    setMessages(prev => [...prev, assistantMessage]);
    setConversationHistory(prev => [...prev, { role: 'assistant', content: apiResponse.response }]);
    setIsTyping(false);

    extractSiteParams(chatInput.trim(), apiResponse.response);
  }, [chatInput, messages, sendToAPI, extractSiteParams]);

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit();
    }
  };

  // Clear chat
  const clearChat = () => {
    setMessages([messages[0]]); // Keep welcome message
    setConversationHistory([]);
  };

  // Styles
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'white',
    },
    header: {
      padding: '12px 16px',
      borderBottom: `1px solid ${COLORS.border}`,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    title: {
      fontSize: '14px',
      fontWeight: '600',
      color: COLORS.textPrimary,
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    messagesArea: {
      flex: 1,
      overflowY: 'auto',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    },
    inputArea: {
      padding: '12px 16px',
      borderTop: `1px solid ${COLORS.border}`,
      display: 'flex',
      gap: '8px',
    },
    input: {
      flex: 1,
      padding: '10px 14px',
      border: `1px solid ${COLORS.border}`,
      borderRadius: '20px',
      fontSize: '14px',
      outline: 'none',
      transition: 'border-color 0.2s',
    },
    sendBtn: {
      padding: '10px 16px',
      backgroundColor: COLORS.accent,
      color: 'white',
      border: 'none',
      borderRadius: '20px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
    },
    clearBtn: {
      padding: '6px 12px',
      backgroundColor: 'transparent',
      color: COLORS.textSecondary,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '12px',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.title}>
          <span>💬</span>
          <span>Chat</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ApiStatusBadge status={apiStatus} />
          <button style={styles.clearBtn} onClick={clearChat}>Clear</button>
        </div>
      </div>

      <div style={styles.messagesArea}>
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={chatEndRef} />
      </div>

      <div style={styles.inputArea}>
        <input
          style={styles.input}
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your site or ask a question..."
          disabled={isTyping}
        />
        <button 
          style={styles.sendBtn} 
          onClick={handleChatSubmit}
          disabled={isTyping || !chatInput.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

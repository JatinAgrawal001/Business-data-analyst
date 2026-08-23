import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { ChatMessage, Dataset } from '../../types';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Database,
  Code2,
  HelpCircle,
  Copy,
  Check,
  Loader2
} from 'lucide-react';
import { DynamicChart } from '../charts/DynamicChart';

interface AIChatProps {
  dataset: Dataset;
}

export const AIChat: React.FC<AIChatProps> = ({ dataset }) => {
  const { showToast } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [copiedSqlId, setCopiedSqlId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadChat = async () => {
      const history = await api.getChatHistory(dataset.id);
      setMessages(history);
    };
    loadChat();
  }, [dataset.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSend = async (queryText?: string) => {
    const text = queryText || inputQuery;
    if (!text.trim() || isSending) return;

    const currentInput = text;
    setInputQuery('');
    setIsSending(true);

    // Optimistically append user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: currentInput,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const aiReply = await api.sendChatMessage(dataset.id, currentInput);
      setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, aiReply]);
    } catch (err: any) {
      showToast('error', 'Chat processing failed', err.message);
    } finally {
      setIsSending(false);
    }
  };

  const copySql = (sql: string, id: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedSqlId(id);
    showToast('info', 'SQL Query Copied to Clipboard');
    setTimeout(() => setCopiedSqlId(null), 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] min-h-[500px] rounded-3xl backdrop-blur-2xl bg-white/[0.04] border border-white/10 shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 backdrop-blur-md bg-white/[0.02] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white font-display">
                InsightFlow Data Analyst
              </h3>
              <span className="text-[10px] font-bold px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-mono">
                Online
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Context: <span className="text-slate-200 font-semibold">{dataset.name}</span> (
              {dataset.rowCount} rows)
            </p>
          </div>
        </div>
      </div>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.length === 0 && !isSending && (
          <div className="flex flex-col items-center justify-center py-10 px-4 text-center max-w-lg mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4 shadow-lg shadow-indigo-500/10">
              <Sparkles className="w-6 h-6" />
            </div>
            <h4 className="text-base font-bold font-display text-white">Ask Your Data</h4>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Explore <span className="text-slate-200 font-semibold">{dataset.name}</span> using deterministic calculations. Inquiries are computed in Python without hallucinating numbers.
            </p>

            <div className="w-full mt-6 space-y-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 block mb-2">
                Click to Analyze
              </span>
              {[
                'What is the highest performing category?',
                'Which segment has the highest total volume?',
                'Why did performance decline in low-performing segments?',
                'What are the primary statistical outliers and anomalies?'
              ].map((starter, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(starter)}
                  className="w-full text-left px-3.5 py-2.5 bg-white/[0.03] hover:bg-indigo-500/15 border border-white/10 hover:border-indigo-500/30 rounded-xl text-xs text-slate-300 hover:text-indigo-200 transition-all flex items-center justify-between group cursor-pointer"
                >
                  <span>{starter}</span>
                  <Sparkles className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                  isUser
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'bg-white/5 border border-white/10 text-indigo-400'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              {/* Message Box */}
              <div
                className={`max-w-[92%] sm:max-w-[85%] min-w-0 rounded-2xl p-4 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20 rounded-tr-none'
                    : 'backdrop-blur-xl bg-white/[0.05] border border-white/10 text-slate-200 shadow-sm rounded-tl-none'
                }`}
              >
                {/* Content */}
                <div className="whitespace-pre-wrap font-sans">
                  {msg.content}
                </div>

                {/* Generated In-Chat Dynamic Chart */}
                {msg.generatedChart && (
                  <div className="mt-4 pt-3 border-t border-white/10 w-full min-w-0">
                    <DynamicChart chart={msg.generatedChart} height={250} />
                  </div>
                )}

                {/* Generated In-Chat SQL Query */}
                {msg.sqlQuery && (
                  <div className="mt-3.5 pt-3 border-t border-white/10">
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1 font-mono">
                      <span className="flex items-center gap-1">
                        <Code2 className="w-3 h-3 text-indigo-400" />
                        <span>Generated Analytical SQL</span>
                      </span>
                      <button
                        onClick={() => copySql(msg.sqlQuery!, msg.id)}
                        className="flex items-center gap-1 hover:text-slate-200 cursor-pointer"
                      >
                        {copiedSqlId === msg.id ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                        <span>{copiedSqlId === msg.id ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <pre className="p-2.5 bg-black/40 rounded-xl border border-white/10 text-[11px] font-mono text-indigo-300 overflow-x-auto">
                      {msg.sqlQuery}
                    </pre>
                  </div>
                )}

                {/* Suggested follow-up pills */}
                {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-white/10">
                    <span className="text-[10px] text-slate-400 block mb-2 font-semibold uppercase tracking-wider font-mono">
                      Suggested Inquiries:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.suggestedQuestions.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(q)}
                          className="px-2.5 py-1 bg-white/5 hover:bg-indigo-500/20 text-indigo-300 hover:text-indigo-200 border border-white/10 hover:border-indigo-500/40 rounded-xl text-[11px] transition-colors cursor-pointer text-left"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isSending && (
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-xl bg-white/5 border border-white/10 text-indigo-400 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-3 text-xs text-slate-300 flex items-center gap-2 backdrop-blur-md">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>Querying dataset statistical models & synthesizing reply...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-white/10 bg-white/[0.02] backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={`Ask anything about ${dataset.name} (${(dataset.columns || []).map((c) => c.key).slice(0, 3).join(', ')})...`}
            className="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isSending}
            className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl shadow-lg shadow-indigo-600/30 transition-all cursor-pointer shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

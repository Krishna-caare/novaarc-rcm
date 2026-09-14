import { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { Bot, Send, Loader2, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  data?: Record<string, unknown>;
  suggestions?: string[];
  timestamp: Date;
}

const SUGGESTED_QUERIES = [
  "What's our AR over 90 days?",
  "Show me top denial codes",
  "What's the denial rate by payer?",
  "Show me collection rate",
  "Compare payer performance",
  "What's our total outstanding AR?",
  "Show claims by status",
  "Which payer has the most denials?",
];

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(SUGGESTED_QUERIES);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Welcome to the NovaArc AI Assistant! I can help you with revenue cycle insights using natural language queries.

**Try asking me things like:**
• "What's our AR over 90 days?"
• "Show me top denial codes"
• "What's the denial rate by payer?"
• "Compare payer performance"
• "What's our collection rate?"

I'll provide instant answers with data from your RCM system.`,
          suggestions: SUGGESTED_QUERIES,
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    const query = input;
    setInput('');
    setLoading(true);
    setSuggestions([]);

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.assistantQuery(query);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        data: response.data,
        suggestions: response.follow_up_suggestions,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setSuggestions(response.follow_up_suggestions || SUGGESTED_QUERIES);
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.response?.data?.detail || 'Unknown error'}. Please try again.`,
        suggestions: SUGGESTED_QUERIES,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setSuggestions(SUGGESTED_QUERIES);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const formatData = (data: Record<string, unknown> | undefined) => {
    if (!data) return null;
    return (
      <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <pre className="text-xs font-mono overflow-x-auto">{JSON.stringify(data, null, 2)}</pre>
      </div>
    );
  };

  return (
          <div className="max-w-4xl mx-auto h-[calc(100vh-200px)] flex flex-col">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary-600" />
            AI Assistant
          </h1>
          <p className="text-slate-600 mt-1">Ask questions about your revenue cycle data in natural language</p>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((message) => (
            <div key={message.id} className={cn('flex gap-3', message.role === 'user' && 'flex-row-reverse')}>
              <div className={cn('w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0', message.role === 'user' ? 'bg-primary-100 text-primary-600' : 'bg-purple-100 text-purple-600')}>
                {message.role === 'user' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                ) : (
                  <Bot className="w-5 h-5" />
                )}
              </div>
              <div className={cn('max-w-[80%]', message.role === 'user' ? 'text-right' : '')}>
                <div className={cn(
                  'px-4 py-2 rounded-2xl',
                  message.role === 'user' 
                    ? 'bg-primary-600 text-white rounded-tr-none' 
                    : 'bg-white text-slate-900 rounded-tl-none border border-slate-200 shadow-sm'
                )}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {formatData(message.data)}
                  {message.suggestions && message.suggestions.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.suggestions.map((s, i) => (
                        <button
                          key={i}
                          onClick={() => handleSuggestionClick(s)}
                          className="text-xs px-3 py-1 bg-slate-100 text-slate-700 rounded-full hover:bg-slate-200 transition-colors"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1">{message.timestamp.toLocaleTimeString()}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {loading && (
          <div className="flex gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-2 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
              <span className="text-sm text-slate-600">Thinking...</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about AR, denials, payers, collections..."
              rows={1}
              className="flex-1 input resize-none min-h-[48px] max-h-32"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="btn-primary flex-shrink-0 h-12"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          {suggestions.length > 0 && !loading && (
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.slice(0, 6).map((s, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSuggestionClick(s)}
                  className="text-xs px-3 py-1.5 bg-slate-100 text-slate-700 rounded-full hover:bg-slate-200 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </form>

        <div className="mt-6 pt-4 border-t border-slate-200">
          <p className="text-sm text-slate-500 text-center">
            <span className="font-medium">Supported Intents:</span>{' '}
            AR Aging, Denial Rates, Top Denial Codes, Payer Comparison, Collection Rates, Total AR, Claims by Status
          </p>
        </div>
      </div>);
}
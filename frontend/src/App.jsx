import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import GeofenceMap from './GeofenceMap';

const TOOL_META = {
  get_weather: { label: 'Weather', color: 'bg-sky-100 text-sky-700', icon: '🌤' },
  geocode_location: { label: 'Geocode', color: 'bg-violet-100 text-violet-700', icon: '📍' },
  search_pois: { label: 'POI Search', color: 'bg-emerald-100 text-emerald-700', icon: '🗺' },
  suggest_geofence: { label: 'Geofence', color: 'bg-amber-100 text-amber-700', icon: '⬡' },
  generate_image: { label: 'Banner', color: 'bg-pink-100 text-pink-700', icon: '🖼' },
};

function ToolBadge({ tool }) {
  const meta = TOOL_META[tool] || { label: tool, color: 'bg-slate-100 text-slate-600', icon: '⚙' };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${meta.color}`}>
      <span>{meta.icon}</span>
      {meta.label}
    </span>
  );
}

function ToolsUsed({ tools }) {
  const [open, setOpen] = useState(false);
  if (!tools?.length) return null;
  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition"
      >
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        Tools used ({tools.length})
      </button>
      {open && (
        <div className="mt-2 flex flex-wrap gap-2">
          {tools.map((tool) => <ToolBadge key={tool} tool={tool} />)}
        </div>
      )}
    </div>
  );
}

const LOADING_HINTS = [
  'Checking location data…',
  'Fetching weather conditions…',
  'Searching nearby POIs…',
  'Calculating geofence…',
  'Building your campaign…',
];

function ThinkingIndicator() {
  const [hintIdx, setHintIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setHintIdx((i) => (i + 1) % LOADING_HINTS.length), 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
        <span className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-2 w-2 rounded-full bg-slate-400"
              style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
            />
          ))}
        </span>
        <span className="text-slate-500 transition-all">{LOADING_HINTS[hintIdx]}</span>
      </div>
    </div>
  );
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function generateSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => {
    return sessionStorage.getItem('session_id') || generateSessionId();
  });

  const messagesEndRef = useRef(null);

  useEffect(() => {
    sessionStorage.setItem('session_id', sessionId);
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const suggestedPrompts = useMemo(
    () => [
      'Check New York weather and suggest a marketing campaign for nearby grocery stores',
      'Find coffee shops near Jersey City NJ and suggest a cold weather activation',
      'Find gyms near Austin TX and suggest a morning workout activation',
    ],
    []
  );

  const sendMessage = useCallback(async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    const userMessage = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const local_time = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', hour12: true, weekday: 'short'
      });

      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: trimmed,
        session_id: sessionId,
        local_time,
      });

      const agentMessage = {
        role: 'agent',
        content: response.data?.response || 'No response received.',
        toolsUsed: Array.isArray(response.data?.tools_used) ? response.data.tools_used : [],
        pois: Array.isArray(response.data?.pois) ? response.data.pois : [],
        geofenceRadiusM: response.data?.geofence_radius_m || null,
        mapCenter: response.data?.map_center || null,
        imageUrl: response.data?.image_url
          ? `${API_BASE_URL}/image-proxy?url=${encodeURIComponent(response.data.image_url)}`
          : null,
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        error?.message ||
        'Something went wrong while contacting the assistant.';

      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          content: `Unable to process your request right now.\n\n${detail}`,
          toolsUsed: [],
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, sessionId]);

  const onInputKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/session/${sessionId}`);
    } catch (_) {
      // best-effort clear on server
    }
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    setInput('');
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <div className="mx-auto flex h-screen w-full max-w-5xl flex-col px-4 py-4 sm:px-6 sm:py-6">
        <header className="mb-4 flex items-center justify-between rounded-xl border border-slate-700 bg-slate-800/80 p-4 shadow-lg shadow-slate-950/30 sm:mb-6 sm:p-5">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">
              Moment Trigger Assistant
            </h1>
            <p className="mt-1 text-sm text-slate-300 sm:text-base">
              Location-Based Marketing Activation Platform
            </p>
          </div>
          <button
            type="button"
            onClick={startNewChat}
            disabled={loading}
            className="rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            New Chat
          </button>
        </header>

        <main className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-700 bg-slate-800/60 shadow-lg shadow-slate-950/30">
          <section className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 sm:p-5">
            {messages.length === 0 && (
              <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
                <p className="mb-3 text-sm font-medium text-slate-300">Suggested prompts</p>
                <div className="space-y-2">
                  {suggestedPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => sendMessage(prompt)}
                      className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-left text-sm text-slate-200 transition hover:border-slate-500 hover:bg-slate-700"
                      disabled={loading}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] rounded-xl px-4 py-3 sm:max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-slate-950 text-slate-100'
                      : message.isError
                        ? 'border border-red-300 bg-red-50 text-red-900'
                        : 'bg-white text-slate-900'
                  }`}
                >
                  {message.role === 'agent' ? (
                    <div className="prose prose-sm max-w-none prose-p:my-1 prose-strong:text-inherit prose-li:my-0.5">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="m-0 whitespace-pre-wrap text-sm sm:text-base">{message.content}</p>
                  )}

                  {message.role === 'agent' && message.pois?.length > 0 && (
                    <GeofenceMap
                      pois={message.pois}
                      geofenceRadiusM={message.geofenceRadiusM}
                      mapCenter={message.mapCenter}
                    />
                  )}

                  {message.role === 'agent' && message.imageUrl && (
                    <div className="mt-4">
                      <p className="mb-2 text-xs font-medium text-slate-400 uppercase tracking-wide">Generated Campaign Banner</p>
                      <div className="relative w-full rounded-xl border border-slate-200 overflow-hidden bg-slate-100" style={{minHeight: '200px'}}>
                        <p className="absolute inset-0 flex items-center justify-center text-xs text-slate-400">Generating image...</p>
                        <img
                          src={message.imageUrl}
                          alt="Generated marketing banner"
                          className="relative w-full rounded-xl"
                          style={{display: 'block'}}
                          onLoad={(e) => { e.target.previousSibling.style.display = 'none'; }}
                          onError={(e) => { e.target.previousSibling.textContent = 'Image unavailable. '; e.target.style.display = 'none'; }}
                        />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        <a href={message.imageUrl} target="_blank" rel="noreferrer" className="underline">Open image in new tab</a>
                      </p>
                    </div>
                  )}

                  <ToolsUsed tools={message.toolsUsed} />
                </div>
              </div>
            ))}

            {loading && <ThinkingIndicator />}

            <div ref={messagesEndRef} />
          </section>

          <section className="border-t border-slate-700 p-4 sm:p-5">
            <div className="flex items-end gap-3">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={onInputKeyDown}
                placeholder="Type your request... (Shift+Enter for new line)"
                rows={2}
                disabled={loading}
                className="min-h-[52px] flex-1 resize-none rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-400 outline-none transition focus:border-slate-400 disabled:cursor-not-allowed disabled:opacity-70"
              />
              <button
                type="button"
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className="h-[52px] rounded-lg bg-white px-4 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                Send
              </button>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;

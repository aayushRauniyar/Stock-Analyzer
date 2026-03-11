import { useState, useCallback } from "react";

// ─── THEME ────────────────────────────────────────────────────────────────────
const THEMES = {
  light: {
    bg: "#fdf8f3", bgAlt: "#f7f0e8", surface: "#faf4ec",
    surfaceHover: "#f0e5d6", border: "rgba(212,99,122,0.13)",
    borderStrong: "rgba(212,99,122,0.3)",
    rose: "#d4637a", roseBg: "#fde8ed", roseGlow: "rgba(212,99,122,0.1)",
    gold: "#c9923a", goldBg: "#fef6e8", goldGlow: "rgba(201,146,58,0.1)",
    moss: "#5e9962", mossBg: "#edf5ee", mossGlow: "rgba(94,153,98,0.1)",
    purple: "#7c5cbf", purpleBg: "#f3eefb",
    up: "#4a9e52", down: "#c0392b",
    text: "#3d2d1e", textSoft: "#6b5542", textMuted: "#a08878", textFaint: "#c8b8ac",
    navBg: "rgba(253,248,243,0.95)", sidebarBg: "#f7f0e8",
    shadow: "0 2px 16px rgba(180,80,100,0.07)",
    shadowMd: "0 4px 28px rgba(180,80,100,0.11)",
    codeBg: "#1a1008",
  },
  dark: {
    bg: "#0c0906", bgAlt: "#110e0a", surface: "#181210",
    surfaceHover: "#221a14", border: "rgba(220,110,130,0.13)",
    borderStrong: "rgba(220,110,130,0.28)",
    rose: "#e8697f", roseBg: "rgba(232,105,127,0.12)", roseGlow: "rgba(232,105,127,0.13)",
    gold: "#e8b86d", goldBg: "rgba(232,184,109,0.1)", goldGlow: "rgba(232,184,109,0.11)",
    moss: "#7ec482", mossBg: "rgba(126,196,130,0.1)", mossGlow: "rgba(126,196,130,0.11)",
    purple: "#a98ee0", purpleBg: "rgba(169,142,224,0.1)",
    up: "#7ec482", down: "#ff6b6b",
    text: "#ede0d4", textSoft: "#c4a898", textMuted: "#7a6458", textFaint: "#3e2e28",
    navBg: "rgba(12,9,6,0.95)", sidebarBg: "#0f0c09",
    shadow: "0 2px 16px rgba(0,0,0,0.35)",
    shadowMd: "0 4px 28px rgba(0,0,0,0.5)",
    codeBg: "#0a0705",
  },
};

// ─── CLAUDE API ───────────────────────────────────────────────────────────────
async function callClaude(system, user, search = false) {
  const body = {
    model: "claude-sonnet-4-20250514", max_tokens: 1000,
    system, messages: [{ role: "user", content: user }],
  };
  if (search) body.tools = [{ type: "web_search_20250305", name: "web_search" }];
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const d = await res.json();
  return (d.content || []).filter(b => b.type === "text").map(b => b.text).join("\n");
}
function safeJSON(raw) {
  try { return JSON.parse(raw.replace(/```json|```/g, "").trim()); } catch { return null; }
}

// ─── SEED DATA ────────────────────────────────────────────────────────────────
const ETF_INFO = {
  SPY: { name: "S&P 500 ETF", desc: "Tracks the S&P 500 index" },
  QQQ: { name: "NASDAQ-100",  desc: "Top 100 non-financial NASDAQ companies" },
  VTI: { name: "Total Market",desc: "Entire US stock market" },
};
const SEED = {
  SPY: { ticker:"SPY", price:531.24, prev:528.60, chg:0.50, rsi:56.2, macd:"BULLISH",  bb:"NEUTRAL",   sma20:"ABOVE", sma50:"ABOVE", hi52:545.32, lo52:492.10, vol:68420000 },
  QQQ: { ticker:"QQQ", price:451.88, prev:453.10, chg:-0.27,rsi:48.7, macd:"BEARISH",  bb:"NEUTRAL",   sma20:"BELOW", sma50:"ABOVE", hi52:503.52, lo52:390.20, vol:42100000 },
  VTI: { ticker:"VTI", price:271.45, prev:270.20, chg:0.46, rsi:53.1, macd:"BULLISH",  bb:"NEUTRAL",   sma20:"ABOVE", sma50:"ABOVE", hi52:285.50, lo52:218.30, vol:3820000  },
};
const SEED_SIG = {
  SPY: { signal:"BUY",  conf:74, risk:"MEDIUM", entry:531.00, exit:545.00, stop:518.00, tf:"MEDIUM", reason:"SMA 20 crossing above SMA 50 with bullish MACD crossover. Volume confirms upward momentum approaching resistance zone.", risks:["Fed rate uncertainty","Earnings season volatility"] },
  QQQ: { signal:"HOLD", conf:58, risk:"MEDIUM", entry:null,   exit:null,   stop:440.00, tf:"SHORT",  reason:"MACD trending bearish below signal line. Price sits below SMA 20 — wait for confirmation before entering.", risks:["Tech sector rotation","Rising yields pressure"] },
  VTI: { signal:"BUY",  conf:68, risk:"LOW",    entry:271.00, exit:282.00, stop:263.00, tf:"LONG",   reason:"Broad market showing steady uptrend with neutral RSI — room to run. Ideal for long-term diversification.", risks:["Broad market correction"] },
};
const POSITIONS = [
  { sym:"SPY", qty:8,  entry:524.30, curr:531.24 },
  { sym:"QQQ", qty:5,  entry:448.10, curr:451.88 },
  { sym:"VTI", qty:12, entry:275.80, curr:271.45 },
];
const TAX_LOG = [
  { date:"2025-03-10", t:"SPY", act:"BUY",  qty:8,  px:524.30, tot:4194.40, why:"MACD crossover · 74% conf" },
  { date:"2025-03-08", t:"QQQ", act:"BUY",  qty:5,  px:448.10, tot:2240.50, why:"RSI oversold bounce · 71% conf" },
  { date:"2025-03-06", t:"VTI", act:"BUY",  qty:12, px:275.80, tot:3309.60, why:"Broad market trend · 68% conf" },
  { date:"2025-03-04", t:"VTI", act:"SELL", qty:6,  px:279.20, tot:1675.20, why:"Stop-loss triggered -3.1%" },
  { date:"2025-02-28", t:"SPY", act:"SELL", qty:4,  px:518.40, tot:2073.60, why:"Exit target reached · 72% conf" },
];

// ─── SPARKLINE ────────────────────────────────────────────────────────────────
function Spark({ up, color, w = 80, h = 28 }) {
  const pts = up
    ? "0,22 14,18 28,20 42,12 56,14 70,6  80,8"
    : "0,6  14,10 28,8  42,18 56,15 70,22 80,24";
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id={`sg${up}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity=".18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline points={pts + ` ${w},${h} 0,${h}`} fill={`url(#sg${up})`} />
      <polyline points={pts} fill="none" stroke={color}
        strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ─── MINI COMPONENTS ─────────────────────────────────────────────────────────
function Pill({ children, color, bg, border }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: "2px 10px", borderRadius: 12,
      fontSize: 9, fontWeight: 700, letterSpacing: "0.14em",
      textTransform: "uppercase", fontFamily: "'Shippori Mincho B1',serif",
      color, background: bg, border: `1px solid ${border || color + "30"}`,
    }}>{children}</span>
  );
}

function Divider({ T }) {
  return <div style={{ height: 1, background: T.border, margin: "6px 0" }} />;
}

function SectionTitle({ jp, en, sub, T }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontFamily: "'Noto Serif JP',serif", fontSize: 10,
        color: T.textMuted, letterSpacing: "0.32em", textTransform: "uppercase",
        marginBottom: 5 }}>{jp}</div>
      <div style={{ fontFamily: "'Zen Old Mincho',serif", fontSize: 22,
        fontWeight: 900, color: T.text, letterSpacing: "0.02em",
        display: "flex", alignItems: "baseline", gap: 12 }}>
        {en}
        {sub && <span style={{ fontSize: 12, fontWeight: 400,
          color: T.textMuted, fontFamily: "'Crimson Pro',serif",
          fontStyle: "italic" }}>{sub}</span>}
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub, subUp, icon, T }) {
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`,
      borderRadius: 12, padding: "16px 18px", boxShadow: T.shadow,
      transition: "all 0.3s" }}>
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ fontFamily: "'Shippori Mincho B1',serif", fontSize: 9,
          letterSpacing: "0.24em", textTransform: "uppercase",
          color: T.textMuted }}>{label}</div>
        <span style={{ fontSize: 15, opacity: 0.65 }}>{icon}</span>
      </div>
      <div style={{ fontFamily: "'Zen Old Mincho',serif", fontSize: 22,
        fontWeight: 900, color: T.text, lineHeight: 1 }}>{value}</div>
      {sub && (
        <div style={{ fontSize: 11, marginTop: 6, fontWeight: 600,
          color: subUp === true ? T.up : subUp === false ? T.down : T.textMuted }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function SignalBadge({ sig, T }) {
  const map = { BUY:[T.up, T.mossBg], SELL:[T.down,"rgba(192,57,43,0.1)"], HOLD:[T.gold, T.goldBg] };
  const [c, bg] = map[sig] || [T.textMuted, T.surface];
  return (
    <span style={{ padding: "4px 14px", borderRadius: 20,
      fontFamily: "'Zen Old Mincho',serif", fontSize: 13, fontWeight: 700,
      letterSpacing: "0.06em", color: c, background: bg,
      border: `1.5px solid ${c}45` }}>{sig}</span>
  );
}

// ─── NAV CONFIG ───────────────────────────────────────────────────────────────
const PAGES = [
  { id: "overview",  icon: "◈",  label: "Overview",    jp: "概要" },
  { id: "market",    icon: "眼",  label: "Market Data", jp: "市場" },
  { id: "signals",   icon: "脳",  label: "AI Signals",  jp: "分析" },
  { id: "positions", icon: "取",  label: "Positions",   jp: "保有" },
  { id: "taxlog",    icon: "税",  label: "Tax Log",     jp: "税務" },
  { id: "modules",   icon: "守",  label: "Modules",     jp: "状態" },
];

// ─────────────────────────────────────────────────────────────────────────────
// MAIN DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [dark, setDark]           = useState(false);
  const [page, setPage]           = useState("overview");
  const [collapsed, setCollapsed] = useState(false);
  const [etf, setEtf]             = useState(SEED);
  const [sig, setSig]             = useState(SEED_SIG);
  const [loading, setLoading]     = useState({});
  const [selTicker, setSelTicker] = useState("SPY");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [mktOpen, setMktOpen]     = useState(false);

  const T = dark ? THEMES.dark : THEMES.light;

  const fetchSignal = useCallback(async (ticker, data) => {
    setLoading(l => ({ ...l, [`s_${ticker}`]: true }));
    try {
      const raw = await callClaude(
        "Expert ETF trading analyst. Respond ONLY with valid JSON, no markdown.",
        `Analyse ${ticker} ETF data: ${JSON.stringify(data)}
Return ONLY:
{"signal":"BUY"|"SELL"|"HOLD","conf":<50-95>,"risk":"LOW"|"MEDIUM"|"HIGH",
"entry":<num|null>,"exit":<num|null>,"stop":<num>,
"tf":"SHORT"|"MEDIUM"|"LONG",
"reason":"<2 concise sentences>","risks":["<r1>","<r2>"]}`
      );
      const d = safeJSON(raw);
      if (d) setSig(prev => ({ ...prev, [ticker]: d }));
    } catch (_) {}
    setLoading(l => ({ ...l, [`s_${ticker}`]: false }));
  }, []);

  // ── transform Python JSON → dashboard format ──────────────────────────────
  const transformTicker = (raw) => ({
    ticker: raw.ticker,
    price: raw.price,
    prev: raw.prev_close,
    chg: raw.daily_change_pct,
    rsi: raw.rsi,
    macd: raw.macd_signal,                       // "BULLISH" / "BEARISH" / "NEUTRAL"
    bb: raw.bb_signal,                           // "OVERBOUGHT" / "OVERSOLD" / "NEUTRAL"
    sma20: raw.above_sma20 ? "ABOVE" : "BELOW", // boolean → string
    sma50: raw.above_sma50 ? "ABOVE" : "BELOW", // boolean → string
    hi52: raw.bb_upper,   // approximate — real 52w high isn't in the JSON yet
    lo52: raw.bb_lower,   // approximate — real 52w low  isn't in the JSON yet
    vol: raw.volume,
    market_open: raw.market_open,
    // keep raw data for AI signal analysis
    _raw: raw,
  });

  // ── fetch live ETF data ────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    setLoading(l => ({ ...l, SPY: true, QQQ: true, VTI: true }));
    try {
      // Append a timestamp to avoid browser caching of the json file
      const res = await fetch(`/data_snapshots/latest_data.json?t=${new Date().getTime()}`);
      if (!res.ok) {
        console.warn("Failed to load local ETF data. Has the Python script run yet? Falling back to seed data.");
        setEtf(prev => ({ ...prev, ...SEED }));
        throw new Error("Failed to load local ETF data.");
      }
      
      const jsonStr = await res.text();
      const snapshot = safeJSON(jsonStr);
      
      if (snapshot && snapshot.data) {
        // Transform each ticker's data to match dashboard field names
        const newData = {};
        for (const t of ["SPY", "QQQ", "VTI"]) {
          if (snapshot.data[t]) {
            newData[t] = transformTicker(snapshot.data[t]);
          }
        }
        setEtf(prev => ({ ...prev, ...newData }));
        
        if (snapshot.market_open !== undefined) {
          setMktOpen(snapshot.market_open);
        }
        
        if (snapshot.fetched_at_aest) {
           setLastUpdate(snapshot.fetched_at_aest);
        } else {
           setLastUpdate(new Date().toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" }));
        }

        // Trigger AI signal fetch for each loaded ticker
        for (const t of ["SPY", "QQQ", "VTI"]) {
          if (newData[t] && !newData[t].error) {
             fetchSignal(t, newData[t]);
          }
        }
      } else {
        console.error("Snapshot data format invalid.", snapshot);
      }
    } catch (e) {
       console.error("Error fetching local ETF data:", e);
    }
    setLoading(l => ({ ...l, SPY: false, QQQ: false, VTI: false }));
  }, [fetchSignal]);

  const fetchETF = useCallback(async (ticker) => {
    // Because the python script generates data for ALL tickers at once, 
    // the simplest approach is to fetch the whole snapshot file here as well, 
    // even if only asking for a single refresh.
    await fetchAll();
  }, [fetchAll]);

  // ── derived portfolio values ───────────────────────────────────────────────
  const totalValue = POSITIONS.reduce((s, p) => s + p.qty * p.curr, 0);
  const totalPnL   = POSITIONS.reduce((s, p) => s + p.qty * (p.curr - p.entry), 0);
  const cash       = 21495.40;

  // ── shared inline styles ──────────────────────────────────────────────────
  const card = {
    background: T.surface, border: `1px solid ${T.border}`,
    borderRadius: 12, padding: "18px 20px", boxShadow: T.shadow,
    transition: "background 0.3s, border-color 0.3s",
  };
  const th = {
    padding: "8px 12px", textAlign: "left",
    fontFamily: "'Shippori Mincho B1',serif",
    fontSize: 8, letterSpacing: "0.22em", textTransform: "uppercase",
    color: T.rose, fontWeight: 400, background: T.roseBg,
  };
  const td = {
    padding: "11px 12px", borderBottom: `1px solid ${T.border}25`,
    fontSize: 12, color: T.textSoft, verticalAlign: "middle",
  };

  const sideW = collapsed ? 56 : 190;

  return (
    <div style={{ display: "flex", height: "100vh",
      background: T.bg, color: T.text,
      fontFamily: "'Crimson Pro',Georgia,serif",
      overflow: "hidden", transition: "background 0.35s, color 0.35s" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&family=Zen+Old+Mincho:wght@700;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Shippori+Mincho+B1:wght@700;800&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
        @keyframes blink  { 0%,100%{opacity:1} 50%{opacity:0.3} }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-thumb { background:${T.border}; border-radius:2px; }
        .hvr:hover { opacity:0.82; transform:translateY(-1px); }
        .row-hvr:hover { background:${T.surfaceHover} !important; }
        .nav-btn:hover { background:${T.surfaceHover} !important; }
      `}</style>

      {/* ══ SIDEBAR ══════════════════════════════════════════════════════════ */}
      <aside style={{
        width: sideW, flexShrink: 0, background: T.sidebarBg,
        borderRight: `1px solid ${T.border}`,
        display: "flex", flexDirection: "column",
        transition: "width 0.28s cubic-bezier(.16,1,.3,1)",
        overflow: "hidden",
      }}>
        {/* Logo */}
        <div style={{ padding: "14px 12px", borderBottom: `1px solid ${T.border}`,
          display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, flexShrink: 0,
            background: `linear-gradient(135deg,${T.rose},${T.gold}80)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 15 }}>🌸</div>
          {!collapsed && (
            <div style={{ overflow: "hidden" }}>
              <div style={{ fontFamily: "'Zen Old Mincho',serif", fontSize: 13,
                fontWeight: 900, color: T.rose, whiteSpace: "nowrap",
                letterSpacing: "0.03em" }}>Mirai ArcSphere</div>
              <div style={{ fontFamily: "'Noto Serif JP',serif", fontSize: 9,
                color: T.textMuted, letterSpacing: "0.15em" }}>未来アークスフィア</div>
            </div>
          )}
        </div>

        {/* Nav links */}
        <nav style={{ flex: 1, padding: "10px 8px", overflowY: "auto" }}>
          {!collapsed && (
            <div style={{ fontFamily: "'Shippori Mincho B1',serif", fontSize: 8,
              letterSpacing: "0.28em", textTransform: "uppercase",
              color: T.textFaint, padding: "4px 6px", marginBottom: 4 }}>
              Navigation
            </div>
          )}
          {PAGES.map(p => {
            const active = page === p.id;
            return (
              <button key={p.id} onClick={() => setPage(p.id)}
                className="nav-btn"
                style={{
                  width: "100%", display: "flex", alignItems: "center",
                  gap: 10, padding: collapsed ? "10px 0" : "9px 10px",
                  justifyContent: collapsed ? "center" : "flex-start",
                  borderRadius: 8, marginBottom: 2, cursor: "pointer",
                  background: active ? T.roseGlow : "transparent",
                  border: `1px solid ${active ? T.borderStrong : "transparent"}`,
                  transition: "all 0.18s",
                }}>
                <span style={{ fontFamily: "'Noto Serif JP',serif",
                  fontSize: 16, color: active ? T.rose : T.textMuted,
                  flexShrink: 0, lineHeight: 1 }}>{p.icon}</span>
                {!collapsed && (
                  <div style={{ textAlign: "left" }}>
                    <div style={{ fontFamily: "'Shippori Mincho B1',serif",
                      fontSize: 11, fontWeight: 700, letterSpacing: "0.05em",
                      color: active ? T.rose : T.textSoft }}>{p.label}</div>
                    <div style={{ fontFamily: "'Noto Serif JP',serif",
                      fontSize: 9, color: T.textMuted,
                      letterSpacing: "0.1em" }}>{p.jp}</div>
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Paper mode badge */}
        <div style={{ padding: "10px 8px", borderTop: `1px solid ${T.border}` }}>
          <div style={{
            padding: collapsed ? "8px 0" : "8px 10px", borderRadius: 8,
            background: T.roseBg, border: `1px solid ${T.border}`,
            display: "flex", alignItems: "center", gap: 8,
            justifyContent: collapsed ? "center" : "flex-start",
          }}>
            <span style={{ fontSize: 12 }}>📄</span>
            {!collapsed && (
              <div>
                <div style={{ fontFamily: "'Shippori Mincho B1',serif",
                  fontSize: 9, letterSpacing: "0.12em",
                  textTransform: "uppercase", color: T.rose }}>Paper Mode</div>
                <div style={{ fontSize: 9, color: T.textMuted }}>No real money</div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ══ RIGHT PANEL ══════════════════════════════════════════════════════ */}
      <div style={{ flex: 1, display: "flex",
        flexDirection: "column", overflow: "hidden" }}>

        {/* ── TOP BAR ───────────────────────────────────────────────────── */}
        <header style={{
          height: 54, background: T.navBg,
          backdropFilter: "blur(14px)", WebkitBackdropFilter: "blur(14px)",
          borderBottom: `1px solid ${T.border}`,
          display: "flex", alignItems: "center",
          padding: "0 22px", gap: 12, flexShrink: 0,
          transition: "background 0.35s",
        }}>
          {/* Collapse toggle */}
          <button onClick={() => setCollapsed(c => !c)} style={{
            background: "none", border: `1px solid ${T.border}`,
            borderRadius: 7, width: 30, height: 30, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: T.textMuted, fontSize: 13, transition: "all 0.2s",
          }}>☰</button>

          {/* Market pill */}
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "4px 12px", borderRadius: 20,
            background: mktOpen ? T.mossGlow : T.roseGlow,
            border: `1px solid ${mktOpen ? T.moss + "50" : T.border}`,
          }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%",
              background: mktOpen ? T.moss : T.textMuted,
              animation: mktOpen ? "blink 2s infinite" : "none" }}/>
            <span style={{ fontFamily: "'Shippori Mincho B1',serif",
              fontSize: 9, letterSpacing: "0.14em", textTransform: "uppercase",
              color: mktOpen ? T.moss : T.textMuted }}>
              {mktOpen ? "Market Open" : "Market Closed"}
            </span>
          </div>

          {lastUpdate && (
            <span style={{ fontSize: 11, color: T.textMuted, fontStyle: "italic" }}>
              Last update: {lastUpdate} ACST
            </span>
          )}

          <div style={{ marginLeft: "auto", display: "flex",
            alignItems: "center", gap: 10 }}>

            {/* Refresh all */}
            <button onClick={fetchAll} className="hvr" disabled={!!Object.values(loading).find(Boolean)}
              style={{
                padding: "6px 16px",
                fontFamily: "'Shippori Mincho B1',serif",
                fontSize: 9, letterSpacing: "0.14em", textTransform: "uppercase",
                background: T.rose, color: "#fff",
                border: "none", borderRadius: 8, cursor: "pointer",
                transition: "all 0.2s", display: "flex",
                alignItems: "center", gap: 6,
              }}>
              <span>🌸</span> Refresh All
            </button>

            {/* Dark mode toggle */}
            <button onClick={() => setDark(d => !d)} style={{
              width: 50, height: 26, borderRadius: 13, position: "relative",
              background: dark
                ? `linear-gradient(135deg,#221a14,${T.rose}50)`
                : `linear-gradient(135deg,#fde8ed,${T.rose}40)`,
              border: `1.5px solid ${T.borderStrong}`,
              cursor: "pointer", transition: "all 0.35s", flexShrink: 0,
            }}>
              <div style={{
                position: "absolute", top: 2,
                left: dark ? 24 : 2,
                width: 18, height: 18, borderRadius: "50%",
                background: T.rose,
                display: "flex", alignItems: "center",
                justifyContent: "center", fontSize: 10,
                transition: "left 0.32s cubic-bezier(.34,1.56,.64,1)",
                boxShadow: `0 1px 6px ${T.rose}60`,
              }}>{dark ? "🌙" : "☀️"}</div>
            </button>
          </div>
        </header>

        {/* ── PAGE CONTENT ──────────────────────────────────────────────── */}
        <main style={{ flex: 1, overflowY: "auto", padding: "24px 26px" }}>

          {/* ════════════════════ OVERVIEW ════════════════════════════════ */}
          {page === "overview" && (
            <div style={{ animation: "fadeUp 0.35s ease" }}>
              <SectionTitle jp="🌸 Overview · 概要" en="Portfolio Dashboard"
                sub="Paper trading account · Adelaide ACST" T={T} />

              {/* KPIs */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)",
                gap: 12, marginBottom: 20 }}>
                <KpiCard label="Portfolio Value" icon="💼"
                  value={`$${totalValue.toLocaleString("en-AU",{minimumFractionDigits:2})}`}
                  T={T} />
                <KpiCard label="Unrealised P&L" icon="📊"
                  value={`${totalPnL>=0?"+":""}$${Math.abs(totalPnL).toFixed(2)}`}
                  sub={`${totalPnL>=0?"+":""}{${((totalPnL/totalValue)*100).toFixed(2)}}% total`}
                  subUp={totalPnL >= 0} T={T} />
                <KpiCard label="Cash Available" icon="💴"
                  value={`$${cash.toLocaleString("en-AU",{minimumFractionDigits:2})}`}
                  sub="Alpaca paper account" T={T} />
                <KpiCard label="Open Positions" icon="🗂"
                  value={POSITIONS.length} sub="SPY · QQQ · VTI" T={T} />
              </div>

              {/* ETF cards row */}
              <div style={{ fontFamily: "'Shippori Mincho B1',serif", fontSize: 9,
                letterSpacing: "0.24em", textTransform: "uppercase",
                color: T.textMuted, marginBottom: 10 }}>
                Live ETF Watch · ETFウォッチ
              </div>
              <div style={{ display: "grid",
                gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginBottom: 20 }}>
                {["SPY","QQQ","VTI"].map(t => {
                  const d = etf[t]; const s = sig[t];
                  const up = d.chg >= 0;
                  const isLoading = loading[t];
                  return (
                    <div key={t} style={{ ...card, position: "relative",
                      overflow: "hidden" }}>
                      <div style={{ position: "absolute", bottom: -10, right: -4,
                        fontFamily: "'Noto Serif JP',serif", fontWeight: 900,
                        fontSize: 60, color: T.rose, opacity: 0.04,
                        pointerEvents: "none", lineHeight: 1 }}>弧</div>

                      <div style={{ display: "flex", justifyContent: "space-between",
                        alignItems: "flex-start", marginBottom: 10 }}>
                        <div>
                          <div style={{ fontFamily: "'Zen Old Mincho',serif",
                            fontSize: 18, fontWeight: 900, color: T.text }}>{t}</div>
                          <div style={{ fontSize: 10, color: T.textMuted,
                            fontFamily: "'Shippori Mincho B1',serif",
                            letterSpacing: "0.08em" }}>{ETF_INFO[t].name}</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontFamily: "'Zen Old Mincho',serif",
                            fontSize: 19, fontWeight: 900, color: T.text }}>
                            ${d.price?.toFixed(2)}
                          </div>
                          <div style={{ fontSize: 12, fontWeight: 700,
                            color: up ? T.up : T.down }}>
                            {up ? "+" : ""}{d.chg?.toFixed(2)}%
                          </div>
                        </div>
                      </div>

                      <Spark up={up} color={up ? T.up : T.down} w={160} h={30} />

                      {/* Indicator pills */}
                      <div style={{ display: "flex", gap: 5, margin: "10px 0" }}>
                        {[
                          { l:"RSI", v:d.rsi, c: d.rsi>70?T.down:d.rsi<30?T.up:T.textMuted },
                          { l:"MACD", v:d.macd, c:d.macd==="BULLISH"?T.up:d.macd==="BEARISH"?T.down:T.gold },
                          { l:"BB", v:d.bb, c:d.bb==="OVERBOUGHT"?T.down:d.bb==="OVERSOLD"?T.up:T.textMuted },
                        ].map(x => (
                          <div key={x.l} style={{ flex: 1, background: T.bgAlt,
                            border: `1px solid ${T.border}`, borderRadius: 7,
                            padding: "5px 4px", textAlign: "center" }}>
                            <div style={{ fontSize: 8, color: T.textMuted,
                              fontFamily: "'Shippori Mincho B1',serif",
                              letterSpacing: "0.1em", textTransform: "uppercase" }}>{x.l}</div>
                            <div style={{ fontSize: 10, fontWeight: 700,
                              color: x.c, marginTop: 2,
                              fontFamily: "'Shippori Mincho B1',serif" }}>{x.v}</div>
                          </div>
                        ))}
                      </div>

                      {s && (
                        <div style={{ display: "flex",
                          justifyContent: "space-between", alignItems: "center" }}>
                          <SignalBadge sig={s.signal} T={T} />
                          <span style={{ fontSize: 11, color: T.textMuted }}>
                            {s.conf}% · {s.risk}
                          </span>
                        </div>
                      )}

                      <button onClick={() => fetchETF(t)}
                        disabled={isLoading}
                        style={{ marginTop: 10, width: "100%", padding: "6px",
                          fontFamily: "'Shippori Mincho B1',serif",
                          fontSize: 8, letterSpacing: "0.16em", textTransform: "uppercase",
                          background: "none", border: `1px solid ${T.border}`,
                          borderRadius: 6, cursor: isLoading ? "wait" : "pointer",
                          color: isLoading ? T.rose : T.textMuted, transition: "all 0.2s" }}>
                        {isLoading ? "🌸 fetching..." : "↻ refresh live"}
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Bottom row */}
              <div style={{ display: "grid",
                gridTemplateColumns: "1.6fr 1fr", gap: 14 }}>
                {/* Recent trades */}
                <div style={card}>
                  <div style={{ fontFamily: "'Shippori Mincho B1',serif",
                    fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase",
                    color: T.textMuted, marginBottom: 12 }}>Recent Trades</div>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead><tr>
                      {["Date","Ticker","Action","Qty","Price","Total"].map(h => (
                        <th key={h} style={th}>{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {TAX_LOG.slice(0,4).map((r,i) => (
                        <tr key={i} className="row-hvr" style={{ transition:"background 0.15s" }}>
                          <td style={td}>{r.date}</td>
                          <td style={{ ...td, fontFamily:"'Zen Old Mincho',serif",
                            fontWeight:900, fontSize:14, color:T.text }}>{r.t}</td>
                          <td style={td}>
                            <Pill color={r.act==="BUY"?T.up:T.down}
                              bg={r.act==="BUY"?T.mossBg:"rgba(192,57,43,0.1)"}>
                              {r.act}
                            </Pill>
                          </td>
                          <td style={td}>{r.qty}</td>
                          <td style={td}>${r.px}</td>
                          <td style={{ ...td, fontWeight:700, color:T.text }}>
                            ${r.tot.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Signal summary */}
                <div style={card}>
                  <div style={{ fontFamily: "'Shippori Mincho B1',serif",
                    fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase",
                    color: T.textMuted, marginBottom: 12 }}>AI Signal Summary</div>
                  {["SPY","QQQ","VTI"].map(t => {
                    const s = sig[t];
                    const sc = s.signal==="BUY"?T.up:s.signal==="SELL"?T.down:T.gold;
                    return (
                      <div key={t} style={{ display:"flex",
                        justifyContent:"space-between", alignItems:"center",
                        padding:"10px 0", borderBottom:`1px solid ${T.border}35` }}>
                        <div>
                          <span style={{ fontFamily:"'Zen Old Mincho',serif",
                            fontWeight:900, fontSize:15, color:T.text }}>{t}</span>
                          <span style={{ fontSize:11, color:T.textMuted,
                            marginLeft:8 }}>{s.risk} risk</span>
                        </div>
                        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                          <span style={{ fontSize:11, color:T.textMuted }}>{s.conf}%</span>
                          <span style={{ padding:"3px 12px", borderRadius:12,
                            fontFamily:"'Zen Old Mincho',serif",
                            fontSize:11, fontWeight:700, color:sc,
                            background:`${sc}15`, border:`1px solid ${sc}40` }}>
                            {s.signal}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════ MARKET DATA ═════════════════════════════ */}
          {page === "market" && (
            <div style={{ animation:"fadeUp 0.35s ease" }}>
              <div style={{ display:"flex", justifyContent:"space-between",
                alignItems:"flex-end", marginBottom:20 }}>
                <SectionTitle jp="Module 1 · 市場データエンジン"
                  en="Live Market Data" T={T} />
                <button onClick={fetchAll} className="hvr" style={{
                  padding:"8px 18px", background:T.rose, color:"#fff",
                  fontFamily:"'Shippori Mincho B1',serif",
                  fontSize:9, letterSpacing:"0.14em", textTransform:"uppercase",
                  border:"none", borderRadius:8, cursor:"pointer", marginBottom:20 }}>
                  🌸 Fetch All Live
                </button>
              </div>

              {/* ETF cards */}
              <div style={{ display:"grid",
                gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:20 }}>
                {["SPY","QQQ","VTI"].map(t => {
                  const d = etf[t]; const up = d.chg >= 0;
                  return (
                    <div key={t} style={card}>
                      <div style={{ display:"flex", justifyContent:"space-between",
                        alignItems:"center", marginBottom:12 }}>
                        <div>
                          <div style={{ fontFamily:"'Zen Old Mincho',serif",
                            fontSize:20, fontWeight:900, color:T.text }}>{t}</div>
                          <div style={{ fontSize:10, color:T.textMuted,
                            fontFamily:"'Shippori Mincho B1',serif" }}>
                            {ETF_INFO[t].desc}
                          </div>
                        </div>
                        <div style={{ textAlign:"right" }}>
                          <div style={{ fontFamily:"'Zen Old Mincho',serif",
                            fontSize:22, fontWeight:900, color:T.text }}>
                            ${d.price?.toFixed(2)}
                          </div>
                          <div style={{ fontSize:13, fontWeight:700,
                            color:up?T.up:T.down }}>
                            {up?"+":""}{d.chg?.toFixed(2)}%
                          </div>
                        </div>
                      </div>
                      <Spark up={up} color={up?T.up:T.down} w={200} h={36} />
                      <div style={{ marginTop:10, display:"grid",
                        gridTemplateColumns:"1fr 1fr", gap:6 }}>
                        {[
                          ["RSI 14",  d.rsi, d.rsi>70?T.down:d.rsi<30?T.up:T.textSoft],
                          ["MACD",    d.macd, d.macd==="BULLISH"?T.up:d.macd==="BEARISH"?T.down:T.gold],
                          ["Bollinger",d.bb, d.bb==="OVERBOUGHT"?T.down:d.bb==="OVERSOLD"?T.up:T.textMuted],
                          ["SMA 20",  d.sma20, d.sma20==="ABOVE"?T.up:T.down],
                          ["SMA 50",  d.sma50, d.sma50==="ABOVE"?T.up:T.down],
                          ["Volume",  d.vol?.toLocaleString(), T.textSoft],
                        ].map(([l,v,c]) => (
                          <div key={l} style={{ background:T.bgAlt,
                            border:`1px solid ${T.border}`, borderRadius:7,
                            padding:"6px 10px", display:"flex",
                            justifyContent:"space-between", alignItems:"center" }}>
                            <span style={{ fontSize:10, color:T.textMuted,
                              fontFamily:"'Shippori Mincho B1',serif",
                              letterSpacing:"0.08em" }}>{l}</span>
                            <span style={{ fontSize:11, fontWeight:700,
                              color:c }}>{v}</span>
                          </div>
                        ))}
                      </div>
                      <div style={{ marginTop:10, display:"flex",
                        justifyContent:"space-between", fontSize:11,
                        color:T.textMuted, padding:"6px 0",
                        borderTop:`1px solid ${T.border}30` }}>
                        <span>52w Low: <strong style={{color:T.down}}>${d.lo52}</strong></span>
                        <span>52w High: <strong style={{color:T.up}}>${d.hi52}</strong></span>
                      </div>
                      <button onClick={()=>fetchETF(t)} disabled={loading[t]}
                        style={{ marginTop:8, width:"100%", padding:"7px",
                          background:"none", border:`1px solid ${T.border}`,
                          borderRadius:7, cursor:loading[t]?"wait":"pointer",
                          fontFamily:"'Shippori Mincho B1',serif",
                          fontSize:8, letterSpacing:"0.16em", textTransform:"uppercase",
                          color:loading[t]?T.rose:T.textMuted }}>
                        {loading[t]?"🌸 fetching live data...":"↻ refresh"}
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Comparison table */}
              <div style={card}>
                <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                  fontSize:9, letterSpacing:"0.22em", textTransform:"uppercase",
                  color:T.textMuted, marginBottom:14 }}>
                  Indicator Comparison Table
                </div>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead><tr>
                    {["ETF","Price","Day Chg","RSI 14","MACD","Bollinger","vs SMA20","vs SMA50","52w Low","52w High"].map(h=>(
                      <th key={h} style={th}>{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {["SPY","QQQ","VTI"].map((t,i)=>{
                      const d=etf[t]; const up=d.chg>=0;
                      return (
                        <tr key={t} className="row-hvr"
                          style={{background:i%2===0?"transparent":T.bgAlt+"80",
                            transition:"background 0.15s"}}>
                          <td style={{...td,fontFamily:"'Zen Old Mincho',serif",
                            fontWeight:900,fontSize:15,color:T.text}}>{t}</td>
                          <td style={{...td,fontWeight:700,color:T.text,
                            fontFamily:"'Zen Old Mincho',serif"}}>${d.price?.toFixed(2)}</td>
                          <td style={{...td,fontWeight:700,color:up?T.up:T.down}}>
                            {up?"+":""}{d.chg?.toFixed(2)}%</td>
                          <td style={{...td,color:d.rsi>70?T.down:d.rsi<30?T.up:T.textSoft}}>
                            {d.rsi}</td>
                          <td style={{...td,color:d.macd==="BULLISH"?T.up:d.macd==="BEARISH"?T.down:T.gold}}>
                            {d.macd}</td>
                          <td style={{...td,color:d.bb==="OVERBOUGHT"?T.down:d.bb==="OVERSOLD"?T.up:T.textMuted}}>
                            {d.bb}</td>
                          <td style={{...td,color:d.sma20==="ABOVE"?T.up:T.down}}>{d.sma20}</td>
                          <td style={{...td,color:d.sma50==="ABOVE"?T.up:T.down}}>{d.sma50}</td>
                          <td style={{...td,color:T.down}}>${d.lo52}</td>
                          <td style={{...td,color:T.up}}>${d.hi52}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════════════ AI SIGNALS ══════════════════════════════ */}
          {page === "signals" && (
            <div style={{ animation:"fadeUp 0.35s ease" }}>
              <div style={{ display:"flex", justifyContent:"space-between",
                alignItems:"flex-end", marginBottom:20 }}>
                <SectionTitle jp="Module 2 · AI分析エンジン" en="AI Signal Analysis"
                  sub="Claude · Anthropic" T={T} />
                <div style={{ display:"flex", gap:6, marginBottom:20 }}>
                  {["SPY","QQQ","VTI"].map(t=>(
                    <button key={t} onClick={()=>setSelTicker(t)} style={{
                      padding:"7px 18px",
                      fontFamily:"'Zen Old Mincho',serif",
                      fontSize:13, fontWeight:900,
                      background:selTicker===t?T.rose:T.surface,
                      color:selTicker===t?"#fff":T.textMuted,
                      border:`1.5px solid ${selTicker===t?T.rose:T.border}`,
                      borderRadius:8, cursor:"pointer", transition:"all 0.2s",
                    }}>{t}</button>
                  ))}
                </div>
              </div>

              <div style={{ display:"grid",
                gridTemplateColumns:"1.1fr 0.9fr", gap:14 }}>

                {/* Signal detail */}
                {(() => {
                  const s = sig[selTicker]; const d = etf[selTicker];
                  const sc = s.signal==="BUY"?T.up:s.signal==="SELL"?T.down:T.gold;
                  return (
                    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
                      <div style={card}>
                        <div style={{ display:"flex", justifyContent:"space-between",
                          alignItems:"flex-start", marginBottom:16 }}>
                          <div>
                            <div style={{ fontFamily:"'Zen Old Mincho',serif",
                              fontSize:16, fontWeight:900, color:T.text }}>
                              {selTicker} AI Signal
                            </div>
                            <div style={{ fontFamily:"'Noto Serif JP',serif",
                              fontSize:10, color:T.textMuted, marginTop:3,
                              letterSpacing:"0.1em" }}>
                              Claude Analysis · 脳
                            </div>
                          </div>
                          <div style={{ textAlign:"right" }}>
                            <SignalBadge sig={s.signal} T={T} />
                            <div style={{ fontSize:11, color:T.textMuted,
                              marginTop:5 }}>{s.conf}% confidence</div>
                          </div>
                        </div>

                        {/* Confidence bar */}
                        <div style={{ marginBottom:14 }}>
                          <div style={{ display:"flex", justifyContent:"space-between",
                            marginBottom:5 }}>
                            <span style={{ fontSize:10, color:T.textMuted,
                              fontFamily:"'Shippori Mincho B1',serif",
                              letterSpacing:"0.12em", textTransform:"uppercase" }}>
                              Confidence
                            </span>
                            <span style={{ fontSize:12, fontWeight:700, color:sc }}>
                              {s.conf}%
                            </span>
                          </div>
                          <div style={{ background:T.bgAlt, borderRadius:4, height:6 }}>
                            <div style={{ width:`${s.conf}%`, height:"100%",
                              borderRadius:4, background:sc,
                              transition:"width 0.8s cubic-bezier(.16,1,.3,1)" }}/>
                          </div>
                          <div style={{ marginTop:5, fontSize:10, color:T.textMuted }}>
                            {s.conf>=70
                              ? "✅ Above 70% threshold — Module 3 would execute"
                              : "⏸ Below 70% threshold — Module 3 would skip"}
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div style={{ background:T.bgAlt, border:`1px solid ${T.border}`,
                          borderRadius:8, padding:"12px 14px", marginBottom:14,
                          fontSize:13, color:T.textSoft, lineHeight:1.78,
                          fontStyle:"italic" }}>
                          "{s.reason}"
                        </div>

                        {/* Price levels */}
                        <div style={{ display:"grid",
                          gridTemplateColumns:"1fr 1fr 1fr", gap:8, marginBottom:14 }}>
                          {[
                            {l:"Entry",  v:s.entry?`$${s.entry}`:"—",  c:T.up},
                            {l:"Target", v:s.exit ?`$${s.exit}` :"—",  c:T.gold},
                            {l:"Stop Loss",v:`$${s.stop}`,             c:T.down},
                          ].map(p=>(
                            <div key={p.l} style={{ background:T.bgAlt,
                              border:`1px solid ${T.border}`,
                              borderRadius:8, padding:"10px 12px",
                              textAlign:"center" }}>
                              <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                                fontSize:8, letterSpacing:"0.18em",
                                textTransform:"uppercase", color:T.textMuted,
                                marginBottom:5 }}>{p.l}</div>
                              <div style={{ fontFamily:"'Zen Old Mincho',serif",
                                fontSize:16, fontWeight:900, color:p.c }}>{p.v}</div>
                            </div>
                          ))}
                        </div>

                        {/* Risk + timeframe */}
                        <div style={{ display:"flex", gap:8, marginBottom:12 }}>
                          <Pill
                            color={s.risk==="LOW"?T.up:s.risk==="HIGH"?T.down:T.gold}
                            bg={s.risk==="LOW"?T.mossBg:s.risk==="HIGH"?"rgba(192,57,43,0.1)":T.goldBg}>
                            {s.risk} RISK
                          </Pill>
                          <Pill color={T.purple} bg={T.purpleBg}>{s.tf} TERM</Pill>
                        </div>

                        {s.risks?.length > 0 && (
                          <>
                            <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                              fontSize:8, letterSpacing:"0.2em", textTransform:"uppercase",
                              color:T.textMuted, marginBottom:8 }}>Key Risks</div>
                            {s.risks.map((r,i)=>(
                              <div key={i} style={{ display:"flex", gap:8,
                                padding:"7px 0", borderBottom:`1px solid ${T.border}30`,
                                fontSize:12, color:T.textSoft }}>
                                <span style={{color:T.gold,flexShrink:0}}>⚠</span>{r}
                              </div>
                            ))}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Right column */}
                <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
                  {/* Re-analyse */}
                  <div style={card}>
                    <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                      fontSize:9, letterSpacing:"0.22em", textTransform:"uppercase",
                      color:T.textMuted, marginBottom:12 }}>
                      Run Fresh Analysis
                    </div>
                    <button onClick={()=>fetchSignal(selTicker,etf[selTicker])}
                      disabled={loading[`s_${selTicker}`]}
                      className="hvr"
                      style={{ width:"100%", padding:"11px",
                        background:loading[`s_${selTicker}`]?T.bgAlt:T.rose,
                        color:loading[`s_${selTicker}`]?T.textMuted:"#fff",
                        fontFamily:"'Shippori Mincho B1',serif",
                        fontSize:9, letterSpacing:"0.16em", textTransform:"uppercase",
                        border:`1.5px solid ${loading[`s_${selTicker}`]?T.border:T.rose}`,
                        borderRadius:8, cursor:loading[`s_${selTicker}`]?"wait":"pointer",
                        transition:"all 0.2s" }}>
                      {loading[`s_${selTicker}`]
                        ? "🌸 Claude is analysing..."
                        : `🤖 Re-Analyse ${selTicker}`}
                    </button>
                    <div style={{ marginTop:10, fontSize:11, color:T.textMuted,
                      lineHeight:1.7, borderTop:`1px solid ${T.border}30`,
                      paddingTop:10 }}>
                      Sends Module 1 market data to Claude AI. Returns a
                      structured signal with entry/exit levels and risk assessment.
                      Signals below 70% confidence are skipped by Module 3.
                    </div>
                  </div>

                  {/* All signals */}
                  <div style={card}>
                    <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                      fontSize:9, letterSpacing:"0.22em", textTransform:"uppercase",
                      color:T.textMuted, marginBottom:12 }}>
                      All Signals Snapshot
                    </div>
                    {["SPY","QQQ","VTI"].map(t=>{
                      const s=sig[t];
                      const sc=s.signal==="BUY"?T.up:s.signal==="SELL"?T.down:T.gold;
                      return (
                        <div key={t} onClick={()=>setSelTicker(t)}
                          className="row-hvr"
                          style={{ display:"flex", justifyContent:"space-between",
                            alignItems:"center", padding:"10px 10px",
                            borderRadius:8, marginBottom:5, cursor:"pointer",
                            background:selTicker===t?T.roseGlow:T.bgAlt,
                            border:`1px solid ${selTicker===t?T.borderStrong:T.border}`,
                            transition:"all 0.18s" }}>
                          <div>
                            <span style={{ fontFamily:"'Zen Old Mincho',serif",
                              fontWeight:900, fontSize:14, color:T.text }}>{t}</span>
                            <span style={{ fontSize:11, color:T.textMuted,
                              marginLeft:8 }}>{s.risk} · {s.tf}</span>
                          </div>
                          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                            <span style={{fontSize:11,color:T.textMuted}}>{s.conf}%</span>
                            <span style={{ padding:"2px 10px", borderRadius:10,
                              fontFamily:"'Zen Old Mincho',serif",
                              fontSize:11, fontWeight:700, color:sc,
                              background:`${sc}18`, border:`1px solid ${sc}40` }}>
                              {s.signal}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════ POSITIONS ═══════════════════════════════ */}
          {page === "positions" && (
            <div style={{ animation:"fadeUp 0.35s ease" }}>
              <SectionTitle jp="Module 3 · 取引実行エンジン" en="Open Positions"
                sub="Paper account · Alpaca Markets" T={T} />

              <div style={{ display:"grid",
                gridTemplateColumns:"repeat(4,1fr)", gap:12, marginBottom:20 }}>
                <KpiCard label="Positions" icon="🗂" value={POSITIONS.length} T={T} />
                <KpiCard label="Market Value" icon="💼"
                  value={`$${totalValue.toFixed(2)}`} T={T} />
                <KpiCard label="Total P&L" icon="📊"
                  value={`${totalPnL>=0?"+":""}$${Math.abs(totalPnL).toFixed(2)}`}
                  subUp={totalPnL>=0}
                  sub={`${((totalPnL/totalValue)*100).toFixed(2)}% unrealised`} T={T} />
                <KpiCard label="Stop-Loss" icon="🛡"
                  value="Active" sub="3% per position" T={T} />
              </div>

              <div style={card}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead><tr>
                    {["Symbol","Description","Shares","Avg Entry","Current","Market Value","Unrealised P&L","Change","Action"].map(h=>(
                      <th key={h} style={th}>{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {POSITIONS.map((p,i)=>{
                      const val=p.qty*p.curr;
                      const pnl=p.qty*(p.curr-p.entry);
                      const pct=((p.curr-p.entry)/p.entry)*100;
                      const up=pnl>=0;
                      return (
                        <tr key={i} className="row-hvr"
                          style={{ background:i%2===0?"transparent":T.bgAlt+"60",
                            transition:"background 0.15s" }}>
                          <td style={{...td,fontFamily:"'Zen Old Mincho',serif",
                            fontWeight:900,fontSize:16,color:T.text}}>{p.sym}</td>
                          <td style={{...td,fontSize:11,color:T.textMuted}}>
                            {ETF_INFO[p.sym].name}
                          </td>
                          <td style={td}>{p.qty}</td>
                          <td style={td}>${p.entry.toFixed(2)}</td>
                          <td style={{...td,fontWeight:700,color:T.text}}>
                            ${p.curr.toFixed(2)}
                          </td>
                          <td style={{...td,fontWeight:600,color:T.text}}>
                            ${val.toFixed(2)}
                          </td>
                          <td style={{...td,fontWeight:700,color:up?T.up:T.down}}>
                            {up?"+":""}${Math.abs(pnl).toFixed(2)}
                          </td>
                          <td style={{...td,fontWeight:700,fontSize:12,
                            color:up?T.up:T.down}}>
                            {up?"+":""}{pct.toFixed(2)}%
                          </td>
                          <td style={td}>
                            <button style={{ padding:"5px 12px",
                              fontFamily:"'Shippori Mincho B1',serif",
                              fontSize:8,letterSpacing:"0.12em",textTransform:"uppercase",
                              background:"rgba(192,57,43,0.1)",color:T.down,
                              border:`1px solid ${T.down}40`,borderRadius:6,
                              cursor:"pointer" }}>
                              Close
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Risk settings */}
              <div style={{ ...card, marginTop:14 }}>
                <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                  fontSize:9,letterSpacing:"0.22em",textTransform:"uppercase",
                  color:T.textMuted,marginBottom:12 }}>
                  Risk Management Settings
                </div>
                <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10 }}>
                  {[
                    {l:"Max Risk/Trade",v:"2.0%",desc:"Of account equity"},
                    {l:"Stop-Loss",v:"3.0%",desc:"Auto-close trigger"},
                    {l:"Daily Loss Limit",v:"5.0%",desc:"Kill-switch level"},
                    {l:"Min AI Confidence",v:"70%",desc:"Trade threshold"},
                  ].map(r=>(
                    <div key={r.l} style={{ background:T.bgAlt,
                      border:`1px solid ${T.border}`,borderRadius:8,
                      padding:"12px 14px" }}>
                      <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                        fontSize:8,letterSpacing:"0.14em",textTransform:"uppercase",
                        color:T.textMuted,marginBottom:6 }}>{r.l}</div>
                      <div style={{ fontFamily:"'Zen Old Mincho',serif",
                        fontSize:20,fontWeight:900,color:T.rose }}>{r.v}</div>
                      <div style={{ fontSize:10,color:T.textMuted,
                        marginTop:4 }}>{r.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════ TAX LOG ══════════════════════════════════ */}
          {page === "taxlog" && (
            <div style={{ animation:"fadeUp 0.35s ease" }}>
              <SectionTitle jp="ATO Compliant · 税務記録" en="Tax Trade Log"
                sub="Australian Tax Office · Adelaide" T={T} />

              <div style={{ display:"grid",
                gridTemplateColumns:"repeat(3,1fr)",gap:12,marginBottom:18 }}>
                <KpiCard label="Total Trades" icon="📋"
                  value={TAX_LOG.length} T={T} />
                <KpiCard label="Total Bought" icon="📥"
                  value={`$${TAX_LOG.filter(r=>r.act==="BUY").reduce((s,r)=>s+r.tot,0).toFixed(2)}`}
                  T={T} />
                <KpiCard label="Total Sold" icon="📤"
                  value={`$${TAX_LOG.filter(r=>r.act==="SELL").reduce((s,r)=>s+r.tot,0).toFixed(2)}`}
                  T={T} />
              </div>

              <div style={{ background:T.goldBg, border:`1px solid ${T.gold}45`,
                borderRadius:10, padding:"13px 18px", marginBottom:16,
                display:"flex",gap:10,alignItems:"flex-start" }}>
                <span style={{fontSize:17,flexShrink:0}}>🏛</span>
                <div style={{fontSize:12,color:T.textSoft,lineHeight:1.75}}>
                  <strong style={{color:T.gold}}>ATO — International Student Note:</strong>{" "}
                  Alpaca is a US broker. Profits may be foreign income, exempt from
                  Australian tax as a temporary resident. Lodge returns
                  <strong> July 1 – October 31</strong> annually via myTax.
                  Use the ATO's free Tax Help Programme if income is under $70,000 AUD.
                </div>
              </div>

              <div style={card}>
                <div style={{ display:"flex",justifyContent:"space-between",
                  alignItems:"center",marginBottom:14 }}>
                  <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                    fontSize:9,letterSpacing:"0.22em",textTransform:"uppercase",
                    color:T.textMuted }}>Trade History · ATO Record</div>
                  <button style={{ padding:"6px 14px",
                    fontFamily:"'Shippori Mincho B1',serif",
                    fontSize:8,letterSpacing:"0.14em",textTransform:"uppercase",
                    background:T.mossBg,color:T.moss,
                    border:`1px solid ${T.moss}40`,borderRadius:7,cursor:"pointer" }}>
                    ↓ Export CSV
                  </button>
                </div>
                <table style={{ width:"100%",borderCollapse:"collapse" }}>
                  <thead><tr>
                    {["Date","Ticker","Action","Qty","Price USD","Total USD","Broker","Mode","AI Reason"].map(h=>(
                      <th key={h} style={th}>{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {TAX_LOG.map((r,i)=>(
                      <tr key={i} className="row-hvr"
                        style={{background:i%2===0?"transparent":T.bgAlt+"60",
                          transition:"background 0.15s"}}>
                        <td style={{...td,fontFamily:"'Shippori Mincho B1',serif",
                          fontSize:11}}>{r.date}</td>
                        <td style={{...td,fontFamily:"'Zen Old Mincho',serif",
                          fontWeight:900,fontSize:15,color:T.text}}>{r.t}</td>
                        <td style={td}>
                          <Pill color={r.act==="BUY"?T.up:T.down}
                            bg={r.act==="BUY"?T.mossBg:"rgba(192,57,43,0.1)"}>
                            {r.act}
                          </Pill>
                        </td>
                        <td style={td}>{r.qty}</td>
                        <td style={td}>${r.px}</td>
                        <td style={{...td,fontWeight:700,color:T.text}}>
                          ${r.tot.toFixed(2)}
                        </td>
                        <td style={{...td,fontSize:11,color:T.textMuted}}>Alpaca</td>
                        <td style={td}>
                          <Pill color={T.gold} bg={T.goldBg}>Paper</Pill>
                        </td>
                        <td style={{...td,fontSize:10,color:T.textMuted,
                          maxWidth:180,overflow:"hidden",
                          textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                          {r.why}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════════════ MODULES STATUS ══════════════════════════ */}
          {page === "modules" && (
            <div style={{ animation:"fadeUp 0.35s ease" }}>
              <SectionTitle jp="System · システム状態" en="Module Status"
                sub="Build progress" T={T} />

              <div style={{ display:"grid",
                gridTemplateColumns:"1fr 1fr",gap:14 }}>
                {[
                  { code:"M1", kanji:"眼", name:"Market Data Engine",
                    nameJp:"市場データエンジン", status:"active",
                    version:"1.0.0", color:T.rose,
                    file:"modules/module1_market_data.py",
                    feats:["fetch_raw_data()","calculate_indicators()","is_market_open()","get_market_schedule() → Adelaide","run_data_scheduler() auto loop","JSON snapshot output"],
                    done:[1,1,1,1,1,1] },
                  { code:"M2", kanji:"脳", name:"AI Analysis Engine",
                    nameJp:"AI分析エンジン", status:"planned",
                    version:"—", color:T.gold,
                    file:"modules/module2_ai_analysis.py",
                    feats:["get_ai_insight()","Confidence filter ≥70%","Risk assessment","Entry/exit price levels","JSON signal output","Prompt tuning & validation"],
                    done:[0,0,0,0,0,0] },
                  { code:"M3", kanji:"手", name:"Trade Execution Engine",
                    nameJp:"取引実行エンジン", status:"planned",
                    version:"—", color:T.moss,
                    file:"modules/module3_trade_executor.py",
                    feats:["place_buy() / place_sell()","calculate_position_size()","check_stop_losses()","check_daily_loss_limit()","ATO tax_trade_log.csv","Paper mode toggle"],
                    done:[0,0,0,0,0,0] },
                  { code:"M4", kanji:"顔", name:"Dashboard UI",
                    nameJp:"ダッシュボード", status:"active",
                    version:"1.0.0", color:T.purple,
                    file:"dashboard/App.jsx",
                    feats:["Overview with KPIs","Market Data tab (live)","AI Signals tab (live)","Positions + P&L tab","Tax Log tab + export","Dark / Light mode toggle"],
                    done:[1,1,1,1,1,1] },
                ].map(m=>{
                  const doneCnt=m.done.reduce((s,v)=>s+v,0);
                  const pct=Math.round(doneCnt/m.done.length*100);
                  const sc = m.status==="active" ? T.up : T.textMuted;
                  return (
                    <div key={m.code} style={{ ...card, position:"relative",
                      overflow:"hidden" }}>
                      <div style={{ position:"absolute", bottom:-12, right:-4,
                        fontFamily:"'Noto Serif JP',serif", fontWeight:900,
                        fontSize:64, color:m.color, opacity:0.05,
                        pointerEvents:"none", lineHeight:1 }}>{m.kanji}</div>

                      <div style={{ display:"flex",gap:12,alignItems:"flex-start",
                        marginBottom:14 }}>
                        <div style={{ width:44,height:44,borderRadius:10,
                          background:`${m.color}18`,
                          border:`1.5px solid ${m.color}38`,
                          display:"flex",flexDirection:"column",
                          alignItems:"center",justifyContent:"center",
                          flexShrink:0 }}>
                          <div style={{ fontFamily:"'Zen Old Mincho',serif",
                            fontSize:11,fontWeight:700,color:m.color }}>{m.code}</div>
                          <div style={{ fontFamily:"'Noto Serif JP',serif",
                            fontSize:15,color:m.color,lineHeight:1 }}>{m.kanji}</div>
                        </div>
                        <div style={{flex:1}}>
                          <div style={{ fontFamily:"'Shippori Mincho B1',serif",
                            fontSize:14,fontWeight:700,color:T.text }}>{m.name}</div>
                          <div style={{ fontFamily:"'Noto Serif JP',serif",
                            fontSize:10,color:T.textMuted,letterSpacing:"0.1em",
                            marginTop:2 }}>{m.nameJp}</div>
                        </div>
                        <div style={{textAlign:"right"}}>
                          <Pill color={sc} bg={`${sc}18`}>
                            {m.status}
                          </Pill>
                          <div style={{fontSize:10,color:T.textMuted,
                            marginTop:5}}>{m.version}</div>
                        </div>
                      </div>

                      {/* Progress */}
                      <div style={{marginBottom:12}}>
                        <div style={{display:"flex",justifyContent:"space-between",
                          marginBottom:5}}>
                          <span style={{fontSize:10,color:T.textMuted}}>
                            {doneCnt}/{m.done.length} features complete
                          </span>
                          <span style={{fontSize:12,fontWeight:700,color:m.color}}>
                            {pct}%
                          </span>
                        </div>
                        <div style={{background:T.bgAlt,borderRadius:4,height:5}}>
                          <div style={{width:`${pct}%`,height:"100%",
                            borderRadius:4,background:m.color,
                            transition:"width 0.8s"}}/>
                        </div>
                      </div>

                      <div style={{display:"grid",
                        gridTemplateColumns:"1fr 1fr",gap:5}}>
                        {m.feats.map((f,i)=>(
                          <div key={i} style={{display:"flex",gap:6,
                            alignItems:"center",padding:"5px 8px",borderRadius:6,
                            background:m.done[i]?`${m.color}0d`:T.bgAlt,
                            border:`1px solid ${m.done[i]?m.color+"22":T.border}`,
                            fontSize:11}}>
                            <span style={{color:m.done[i]?m.color:T.textFaint,
                              flexShrink:0,fontSize:10,fontWeight:700}}>
                              {m.done[i]?"✓":"○"}
                            </span>
                            <span style={{color:m.done[i]?T.textSoft:T.textMuted,
                              overflow:"hidden",textOverflow:"ellipsis",
                              whiteSpace:"nowrap",fontFamily:"'Crimson Pro',monospace"}}>
                              {f}
                            </span>
                          </div>
                        ))}
                      </div>

                      <div style={{marginTop:10,padding:"6px 10px",
                        background:T.codeBg,borderRadius:6,
                        fontFamily:"monospace",fontSize:10,color:T.textMuted}}>
                        📁 {m.file}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

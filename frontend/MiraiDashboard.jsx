import { useState, useCallback, useEffect, useRef } from "react";

// ── FONT ──────────────────────────────────────────────────────────────────────
const FONT_IMPORT = `@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');`;

// ── CONSTANTS ─────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:5000/api";

// ── BLOOMBERG COLOR SYSTEM ────────────────────────────────────────────────────
const C = {
  bg:       "#0A0A0A",
  panel:    "#111111",
  panelAlt: "#161616",
  border:   "#1E1E1E",
  border2:  "#282828",
  orange:   "#FF6600",
  orangeDim:"#CC5200",
  green:    "#00CC44",
  greenDim: "#009933",
  red:      "#FF2244",
  redDim:   "#CC1133",
  amber:    "#FFAA00",
  text:     "#E0E0E0",
  textSoft: "#AAAAAA",
  textMuted:"#666666",
  textFaint:"#3A3A3A",
};

// ── SEED DATA ─────────────────────────────────────────────────────────────────
const SEED_MARKET = {
  SPY: { ticker:"SPY", name:"S&P 500 ETF TRUST",  price:531.24, prev:528.60, chg:0.50,  rsi:56.2, macd:"BULLISH", bb:"NEUTRAL", sma20:"ABOVE", sma50:"ABOVE", hi52:545.32, lo52:492.10, vol:68420000 },
  QQQ: { ticker:"QQQ", name:"NASDAQ 100 ETF",    price:451.88, prev:453.10, chg:-0.27, rsi:48.7, macd:"BEARISH", bb:"NEUTRAL", sma20:"BELOW", sma50:"ABOVE", hi52:503.52, lo52:390.20, vol:42100000 },
  VTI: { ticker:"VTI", name:"TOTAL STOCK MARKET",price:271.45, prev:270.20, chg:0.46,  rsi:53.1, macd:"BULLISH", bb:"NEUTRAL", sma20:"ABOVE", sma50:"ABOVE", hi52:285.50, lo52:218.30, vol:3820000  },
};
const SEED_SIG = {
  SPY: { signal:"BUY",  conf:74, risk:"MEDIUM", entry:531.00, exit:545.00, stop:518.00, tf:"MEDIUM TERM", reason:"SMA 20 crossing above SMA 50 with bullish MACD crossover. Volume confirms upward momentum." },
  QQQ: { signal:"HOLD", conf:58, risk:"MEDIUM", entry:null,   exit:null,   stop:440.00, tf:"SHORT TERM",  reason:"MACD trending bearish below signal line. Price sits below SMA 20 — wait for confirmation." },
  VTI: { signal:"BUY",  conf:68, risk:"LOW",    entry:271.00, exit:282.00, stop:263.00, tf:"LONG TERM",   reason:"Broad market showing steady uptrend with neutral RSI — room to run." },
};
const POSITIONS = [
  { sym:"SPY", qty:8,  entry:524.30, curr:531.24 },
  { sym:"QQQ", qty:5,  entry:448.10, curr:451.88 },
  { sym:"VTI", qty:12, entry:275.80, curr:271.45 },
];
const TAX_LOG = [
  { date:"2025-03-10", t:"SPY", act:"BUY",  qty:8,  px:524.30, tot:4194.40, why:"MACD CROSSOVER · 74% CONF" },
  { date:"2025-03-08", t:"QQQ", act:"BUY",  qty:5,  px:448.10, tot:2240.50, why:"RSI OVERSOLD BOUNCE · 71% CONF" },
  { date:"2025-03-06", t:"VTI", act:"BUY",  qty:12, px:275.80, tot:3309.60, why:"BROAD MARKET TREND · 68% CONF" },
  { date:"2025-03-04", t:"VTI", act:"SELL", qty:6,  px:279.20, tot:1675.20, why:"STOP-LOSS TRIGGERED -3.1%" },
  { date:"2025-02-28", t:"SPY", act:"SELL", qty:4,  px:518.40, tot:2073.60, why:"EXIT TARGET REACHED · 72% CONF" },
];
const RECS = [
  { t:"NVDA", reason:"BULLISH MOMENTUM", conf:92, act:"BUY",  risk:"MEDIUM", p:892.45 },
  { t:"AAPL", reason:"SECTOR BREAKOUT",  conf:88, act:"BUY",  risk:"LOW",    p:189.30 },
  { t:"MSFT", reason:"RELATIVE STRENGTH",conf:85, act:"HOLD", risk:"LOW",    p:420.10 },
  { t:"AMD",  reason:"AI CATALYST",      conf:79, act:"BUY",  risk:"HIGH",   p:192.50 },
];


// ── NAV PAGES ─────────────────────────────────────────────────────────────────
const PAGES = [
  { id:"overview",  code:"01", label:"OVERVIEW"  },
  { id:"market",    code:"02", label:"MARKET"    },
  { id:"signals",   code:"03", label:"SIGNALS"   },
  { id:"trading",   code:"04", label:"TRADING"   },
  { id:"positions", code:"05", label:"POSITIONS" },
  { id:"taxlog",    code:"06", label:"TAX LOG"   },
  { id:"orders",     code:"07", label:"ORDERS"    },
];


// ── SPARKLINE ─────────────────────────────────────────────────────────────────
function Spark({ up, w = 100, h = 28 }) {
  const color = up ? C.green : C.red;
  const pts = up
    ? "0,22 14,18 28,20 42,12 56,14 70,6  100,8"
    : "0,6  14,10 28,8  42,18 56,15 70,22 100,24";
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ display:"block" }}>
      <polyline points={pts} fill="none" stroke={color}
        strokeWidth="1.5" strokeLinecap="square" strokeLinejoin="miter" />
    </svg>
  );
}

// ── DIVIDER ───────────────────────────────────────────────────────────────────
function HR({ my = 12 }) {
  return <div style={{ height:1, background:C.border, margin:`${my}px 0` }} />;
}

// ── LABEL ─────────────────────────────────────────────────────────────────────
function Label({ children, color = C.orange }) {
  return (
    <div style={{
      fontFamily:"'IBM Plex Mono', monospace",
      fontSize: 10, letterSpacing:"0.08em",
      textTransform:"uppercase", color, marginBottom:4,
    }}>
      {children}
    </div>
  );
}

// ── SIGNAL TAG ────────────────────────────────────────────────────────────────
function SigTag({ sig }) {
  const map = { BUY:[C.green, "#001A08"], SELL:[C.red, "#1A0008"], HOLD:[C.amber, "#1A1000"] };
  const [fg, bg] = map[sig] || [C.textMuted, C.panel];
  return (
    <span style={{
      fontFamily:"'IBM Plex Mono', monospace",
      fontSize:11, fontWeight:700, letterSpacing:"0.08em",
      color:fg, background:bg, border:`1px solid ${fg}`,
      padding:"2px 8px", display:"inline-block",
    }}>
      {sig}
    </span>
  );
}

// ── BTN ───────────────────────────────────────────────────────────────────────
function Btn({ children, onClick, disabled, style = {}, primary }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      fontFamily:"'IBM Plex Mono', monospace",
      fontSize:10, letterSpacing:"0.1em", textTransform:"uppercase",
      padding:"5px 14px", cursor: disabled ? "wait" : "pointer",
      background: primary ? C.orange : "transparent",
      color:       primary ? "#000" : C.orange,
      border:`1px solid ${C.orange}`, borderRadius:0,
      transition:"background 0.1s, color 0.1s",
      ...style,
    }}>
      {children}
    </button>
  );
}

// ── STAT BOX ──────────────────────────────────────────────────────────────────
function StatBox({ label, value, sub, subColor }) {
  return (
    <div style={{
      background:C.panel, border:`1px solid ${C.border}`,
      padding:"12px 14px",
    }}>
      <Label>{label}</Label>
      <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:20, fontWeight:700, color:C.text, lineHeight:1.2 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:11, color:subColor || C.textSoft, marginTop:4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ── SECTION HEADER ────────────────────────────────────────────────────────────
function SectionHeader({ children }) {
  return (
    <div style={{
      fontFamily:"'IBM Plex Mono', monospace",
      fontSize:10, letterSpacing:"0.12em", textTransform:"uppercase",
      color:C.orange, borderBottom:`1px solid ${C.orange}`,
      paddingBottom:4, marginBottom:12,
    }}>
      {children}
    </div>
  );
}

// ── ETF PANEL ─────────────────────────────────────────────────────────────────
function EtfPanel({ d, s, onRefresh, loading }) {
  const up = d.chg >= 0;
  const chgColor = up ? C.green : C.red;
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, padding:"12px 14px" }}>
      {/* Header row */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
        <div>
          <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:20, fontWeight:700, color:C.orange, letterSpacing:"0.04em" }}>
            {d.ticker}
          </div>
          <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:9, color:C.textMuted, textTransform:"uppercase", letterSpacing:"0.06em" }}>
            {d.name}
          </div>
        </div>
        <div style={{ textAlign:"right" }}>
          <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:20, fontWeight:700, color:C.text }}>
            ${d.price?.toFixed(2)}
          </div>
          <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:12, fontWeight:600, color:chgColor }}>
            {up ? "+" : ""}{d.chg?.toFixed(2)}%
          </div>
        </div>
      </div>

      <div style={{ margin:"8px 0" }}>
        <Spark up={up} w={220} h={26} />
      </div>

      <HR my={8} />

      {/* Indicators */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:6 }}>
        {[
          ["RSI (14)", d.rsi?.toFixed(1), d.rsi > 70 ? C.red : d.rsi < 30 ? C.green : C.textSoft],
          ["MACD",     d.macd,           d.macd === "BULLISH" ? C.green : d.macd === "BEARISH" ? C.red : C.amber],
          ["BB",       d.bb,             d.bb === "OVERBOUGHT" ? C.red : d.bb === "OVERSOLD" ? C.green : C.textSoft],
        ].map(([lbl, val, col]) => (
          <div key={lbl} style={{ background:C.bg, border:`1px solid ${C.border}`, padding:"5px 8px" }}>
            <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:9, color:C.orange, textTransform:"uppercase", letterSpacing:"0.08em" }}>{lbl}</div>
            <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:11, fontWeight:600, color:col, marginTop:2 }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Signal row */}
      {s && (
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:10 }}>
          <SigTag sig={s.signal} />
          <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:11, color:C.textSoft }}>
            {s.conf}% · {s.risk} RISK
          </div>
        </div>
      )}

      <button onClick={onRefresh} disabled={loading} style={{
        marginTop:10, width:"100%", padding:"4px",
        fontFamily:"'IBM Plex Mono', monospace",
        fontSize:9, letterSpacing:"0.12em", textTransform:"uppercase",
        background:"transparent", border:`1px solid ${C.border2}`,
        color:loading ? C.orange : C.textMuted,
        cursor:loading ? "wait" : "pointer",
      }}>
        {loading ? "FETCHING..." : "REFRESH"}
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage]                   = useState("overview");
  const [mkt, setMkt]                     = useState(SEED_MARKET);
  const [sig, setSig]                     = useState(SEED_SIG);
  const [loading, setLoading]             = useState({});
  const [lastUpdate, setLastUpdate]       = useState(null);
  const [mktOpen, setMktOpen]             = useState(false);
  const [streamActive, setStreamActive]   = useState(false);
  const [autoTrade, setAutoTrade]         = useState(false);
  const [autoStatus, setAutoStatus]       = useState("DISABLED");
  const [positions, setPositions]         = useState(POSITIONS);
  const [watchlist, setWatchlist]         = useState([]);
  const [orders, setOrders]               = useState([]);
  const [newTicker, setNewTicker]         = useState("");
  const [tradeForm, setTradeForm]         = useState({ ticker:"SPY", side:"BUY", qty:1, auto_size: false });
  const [tradeMsg, setTradeMsg]           = useState(null);
  const [taxLog, setTaxLog]               = useState(TAX_LOG);
  const sseRef = useRef(null);


  // Derived portfolio
  const totalValue = positions.reduce((s,p) => s + p.qty * p.curr, 0);
  const totalPnL   = positions.reduce((s,p) => s + p.qty * (p.curr - p.entry), 0);
  const cash       = 21495.40;
  const pnlColor   = totalPnL >= 0 ? C.green : C.red;

  // ── Fetch helpers ──────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    setLoading(l => ({ ...l, ALL:true }));
    try {
      const [mktRes, sigRes, posRes, wlRes, ordRes, taxRes] = await Promise.all([
        fetch(`${API_BASE}/market-data?t=${Date.now()}`),
        fetch(`${API_BASE}/signals`),
        fetch(`${API_BASE}/positions`),
        fetch(`${API_BASE}/watchlist`),
        fetch(`${API_BASE}/orders`),
        fetch(`${API_BASE}/tax-log`)
      ]);
      
      if (mktRes.ok) {
        const snap = await mktRes.json();
        if (snap?.data) setMkt(p => ({ ...p, ...snap.data }));
        if (snap?.market_open !== undefined) setMktOpen(snap.market_open);
        if (snap?.fetched_at_aest) setLastUpdate(snap.fetched_at_aest);
      }
      if (sigRes.ok) {
        const sd = await sigRes.json();
        if (sd?.signals) setSig(p => ({ ...p, ...sd.signals }));
      }
      if (posRes.ok) {
        const pd = await posRes.json();
        setPositions(pd.map(p => ({ sym:p.ticker, qty:p.qty, entry:p.entry_price, curr:p.current_price, side:p.side })));
      }
      if (wlRes.ok) {
        const wd = await wlRes.json();
        setWatchlist(wd.watchlist || []);
      }
      if (ordRes.ok) {
        const od = await ordRes.json();
        setOrders(od.orders || []);
      }
      if (taxRes.ok) {
        const td = await taxRes.json();
        setTaxLog(td || []);
      }
    } catch (_) {}
    setLoading(l => ({ ...l, ALL:false }));
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(l => ({ ...l, ALL:true }));
    try {
      const res = await fetch(`${API_BASE}/refresh`, { method:"POST" });
      if (res.ok) {
        const r = await res.json();
        if (r.market_data) setMkt(p => ({ ...p, ...r.market_data }));
        if (r.signals) setSig(p => ({ ...p, ...r.signals }));
        if (r.market_open !== undefined) setMktOpen(r.market_open);
        setLastUpdate(new Date().toLocaleTimeString("en-AU", { hour:"2-digit", minute:"2-digit" }));
        fetchAll(); // Full sync
      }
    } catch (_) { await fetchAll(); }
    setLoading(l => ({ ...l, ALL:false }));
  }, [fetchAll]);

  const handleAddWatchlist = async () => {
    if (!newTicker) return;
    try {
      const resp = await fetch(`${API_BASE}/watchlist/add`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ ticker: newTicker })
      });
      if (resp.ok) {
        setNewTicker("");
        fetchAll();
      }
    } catch(e) {}
  };

  const handleRemoveWatchlist = async (ticker) => {
    try {
      await fetch(`${API_BASE}/watchlist/remove`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ ticker })
      });
      fetchAll();
    } catch(e) {}
  };


  // ── SSE ────────────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchAll();
    const es = new EventSource(`${API_BASE}/stream`);
    sseRef.current = es;
    es.addEventListener("connected",  () => setStreamActive(true));
    es.addEventListener("heartbeat",  () => setStreamActive(true));
    es.addEventListener("update", e => {
      try {
        const d = JSON.parse(e.data);
        if (d.market_data) setMkt(p => ({ ...p, ...d.market_data }));
        if (d.signals) setSig(p => ({ ...p, ...d.signals }));
        if (d.updated_at) setLastUpdate(d.updated_at);
      } catch (_) {}
    });
    es.onerror = () => setStreamActive(false);
    return () => { es.close(); sseRef.current = null; };
  }, []);

  // ── Auto-trade toggle ──────────────────────────────────────────────────────
  const toggleAutoTrade = async () => {
    const endpoint = autoTrade ? "/auto-trade/disable" : "/auto-trade/enable";
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, { method:"POST" });
      if (res.ok) {
        const d = await res.json();
        setAutoTrade(!autoTrade);
        setAutoStatus(d.status || (autoTrade ? "DISABLED" : "ENABLED"));
      }
    } catch (_) {
      setAutoTrade(a => !a);
      setAutoStatus(autoTrade ? "DISABLED" : "ENABLED");
    }
  };

  // ── Manual trade ───────────────────────────────────────────────────────────
  const submitTrade = async () => {
    setTradeMsg("STAGING ORDER...");
    try {
      const res = await fetch(`${API_BASE}/trade`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify(tradeForm),
      });
      const data = await res.json();
      if (res.ok) {
        setTradeMsg(`FILLED — ORDER ID: ${data.order_id}`);
        fetchAll();
      } else {
        setTradeMsg(`REJECTED — ${data.error || res.status}`);
      }
    } catch (e) {
      setTradeMsg(`SYSTEM ERROR — ${e.message}`);
    }
    setTimeout(() => setTradeMsg(null), 5000);
  };


  // ── Styles ─────────────────────────────────────────────────────────────────
  const panelCard = { background:C.panel, border:`1px solid ${C.border}`, padding:"14px" };
  const monoSm    = { fontFamily:"'IBM Plex Mono', monospace", fontSize:11 };
  const th        = { ...monoSm, color:C.orange, textTransform:"uppercase", letterSpacing:"0.08em", padding:"6px 10px", textAlign:"left", fontWeight:600, borderBottom:`1px solid ${C.border}`, background:C.panelAlt };
  const td        = { ...monoSm, color:C.textSoft, padding:"7px 10px", borderBottom:`1px solid ${C.border}` };

  return (
    <div style={{ display:"flex", height:"100vh", background:C.bg, color:C.text, fontFamily:"'IBM Plex Mono', monospace", overflow:"hidden" }}>
      <style>{`
        ${FONT_IMPORT}
        * { box-sizing:border-box; margin:0; padding:0; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        ::-webkit-scrollbar { width:4px; height:4px; background:${C.bg}; }
        ::-webkit-scrollbar-thumb { background:${C.border2}; }
        button:hover:not(:disabled) { opacity:0.8; }
        input, select { background:${C.bg}; border:1px solid ${C.border2}; color:${C.text}; font-family:'IBM Plex Mono',monospace; font-size:12px; padding:5px 8px; outline:none; border-radius:0; }
        input:focus, select:focus { border-color:${C.orange}; }
      `}</style>

      {/* ══ SIDEBAR ═══════════════════════════════════════════════════════════ */}
      <aside style={{ width:180, flexShrink:0, background:C.panel, borderRight:`1px solid ${C.border}`, display:"flex", flexDirection:"column" }}>
        {/* Brand */}
        <div style={{ padding:"14px 14px 10px", borderBottom:`1px solid ${C.border}` }}>
          <div style={{ fontSize:13, fontWeight:700, color:C.orange, letterSpacing:"0.06em" }}>MIRAI ARCSPHERE</div>
          <div style={{ fontSize:9, color:C.textMuted, letterSpacing:"0.1em", marginTop:2 }}>TRADING TERMINAL v1.0</div>
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:"8px 6px" }}>
          {PAGES.map(p => {
            const active = page === p.id;
            return (
              <button key={p.id} onClick={() => setPage(p.id)} style={{
                display:"block", width:"100%", textAlign:"left",
                padding:"8px 8px", marginBottom:2, cursor:"pointer",
                background: active ? `${C.orange}18` : "transparent",
                border:`1px solid ${active ? C.orange : "transparent"}`,
                color: active ? C.orange : C.textSoft,
                fontFamily:"'IBM Plex Mono', monospace",
                fontSize:11, letterSpacing:"0.08em",
                transition:"all 0.1s",
              }}>
                <span style={{ color:C.textMuted, marginRight:8 }}>{p.code}</span>
                {p.label}
              </button>
            );
          })}
        </nav>

        {/* Paper mode */}
        <div style={{ padding:"10px 14px", borderTop:`1px solid ${C.border}` }}>
          <div style={{ fontSize:9, color:C.amber, letterSpacing:"0.1em", textTransform:"uppercase" }}>◆ PAPER MODE</div>
          <div style={{ fontSize:9, color:C.textMuted, marginTop:2 }}>NO REAL MONEY</div>
        </div>
      </aside>

      {/* ══ RIGHT PANEL ═══════════════════════════════════════════════════════ */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>

        {/* ── TOP BAR ────────────────────────────────────────────────────── */}
        <header style={{ height:38, background:C.panel, borderBottom:`1px solid ${C.border}`, display:"flex", alignItems:"center", padding:"0 16px", gap:16, flexShrink:0 }}>
          {/* Market status */}
          <div style={{ display:"flex", alignItems:"center", gap:6 }}>
            <div style={{ width:6, height:6, background: mktOpen ? C.green : C.textMuted, animation: mktOpen ? "blink 2s infinite" : "none" }} />
            <span style={{ fontSize:9, color: mktOpen ? C.green : C.textMuted, letterSpacing:"0.1em" }}>
              MARKET {mktOpen ? "OPEN" : "CLOSED"}
            </span>
          </div>

          {/* Stream */}
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:5, height:5, background: streamActive ? C.green : C.textMuted, animation: streamActive ? "blink 1.5s infinite" : "none" }} />
            <span style={{ fontSize:8, color:C.textMuted, letterSpacing:"0.08em" }}>SSE {streamActive ? "LIVE" : "OFFLINE"}</span>
          </div>

          {lastUpdate && (
            <span style={{ fontSize:9, color:C.textMuted, letterSpacing:"0.06em" }}>LAST: {lastUpdate} ACST</span>
          )}

          {/* Page title */}
          <div style={{ flex:1, textAlign:"center", fontSize:11, fontWeight:600, color:C.textMuted, letterSpacing:"0.12em" }}>
            {PAGES.find(p => p.id === page)?.code ?? "01"} — {PAGES.find(p => p.id === page)?.label ?? "OVERVIEW"}
          </div>

          <Btn onClick={refreshAll} disabled={Object.values(loading).some(Boolean)} primary>
            REFRESH ALL
          </Btn>
        </header>

        {/* ── PAGE CONTENT ───────────────────────────────────────────────── */}
        <main style={{ flex:1, overflowY:"auto", padding:"16px 18px" }}>

          {/* ════════════ OVERVIEW ══════════════════════════════════════════ */}
          {page === "overview" && (
            <div>
              {/* Stat row */}
              <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8, marginBottom:12 }}>
                <StatBox label="PORTFOLIO VALUE"  value={`$${totalValue.toLocaleString("en-AU",{minimumFractionDigits:2})}`} />
                <StatBox label="UNREALISED P&L"
                  value={`${totalPnL>=0?"+":""}$${Math.abs(totalPnL).toFixed(2)}`}
                  sub={`${totalPnL>=0?"+":""}${((totalPnL/totalValue)*100).toFixed(2)}% TOTAL`}
                  subColor={pnlColor} />
                <StatBox label="CASH AVAILABLE"  value={`$${cash.toLocaleString("en-AU",{minimumFractionDigits:2})}`} sub="ALPACA PAPER ACCOUNT" />
                <StatBox label="WATCHLIST SIZE"   value={watchlist.length} sub={`${watchlist.slice(0,3).join(", ")}${watchlist.length > 3 ? "..." : ""}`} />
              </div>

              {/* Watchlist Manager */}
              <div style={{ ...panelCard, marginBottom:12, display:"flex", alignItems:"center", gap:12 }}>
                <Label color={C.amber}>ADD TICKER TO WATCHLIST</Label>
                <div style={{ display:"flex", gap:6 }}>
                  <input type="text" value={newTicker} placeholder="e.g. TSLA, NVDA"
                    onChange={e => setNewTicker(e.target.value.toUpperCase())}
                    onKeyDown={e => e.key === 'Enter' && handleAddWatchlist()}
                    style={{ width:120 }} />
                  <Btn onClick={handleAddWatchlist} primary disabled={!newTicker}>ADD</Btn>
                </div>
                <div style={{ flex:1 }} />
                <div style={{ fontSize:9, color:C.textMuted }}>Total pairs: {watchlist.length}</div>
              </div>

              {/* Live Watchboard */}
              <div style={{ fontFamily:"'IBM Plex Mono', monospace", fontSize:8, color:C.textMuted, letterSpacing:"0.1em", marginBottom:8 }}>
                ── LIVE WATCHBOARD ─────────────────────────────────────────────────────────────
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8, marginBottom:12 }}>
                {watchlist.map(t => (
                  <div key={t} style={{ position:"relative" }}>
                    <EtfPanel d={mkt[t] || { ticker:t, chg:0, price:0 }} s={sig[t]}
                      onRefresh={refreshAll} loading={!!loading.ALL} />
                    <button onClick={() => handleRemoveWatchlist(t)} style={{
                      position:"absolute", top:4, right:4, background:"rgba(255,34,68,0.1)", border:`1px solid ${C.red}`,
                      color:C.red, fontSize:8, padding:"1px 4px", cursor:"pointer"
                    }}>X</button>
                  </div>
                ))}
              </div>

              {/* Bottom section: Trades, Signals, and Recommendations */}
              <div style={{ display:"grid", gridTemplateColumns:"1.6fr 1fr", gap:8 }}>
                {/* Recent trades */}
                <div style={panelCard}>
                  <SectionHeader>RECENT TRADES</SectionHeader>
                  <table style={{ width:"100%", borderCollapse:"collapse" }}>
                    <thead>
                      <tr>{["DATE","TICKER","ACTION","QTY","PRICE","TOTAL"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                    </thead>
                    <tbody>
                      {taxLog.length === 0 ? (
                        <tr><td colSpan="6" style={{ ...td, textAlign:"center" }}>NO RECENT TRADES</td></tr>
                      ) : (
                        taxLog.slice(0,5).map((r,i) => (
                          <tr key={i}>
                            <td style={td}>{r.date}</td>
                            <td style={{ ...td, color:C.orange, fontWeight:600 }}>{r.t}</td>
                            <td style={{ ...td, color: r.act==="BUY" ? C.green : C.red, fontWeight:600 }}>{r.act}</td>
                            <td style={td}>{r.qty}</td>
                            <td style={td}>${r.px.toFixed(2)}</td>
                            <td style={{ ...td, color:C.text, fontWeight:600 }}>${r.tot.toFixed(2)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {/* AI Signal summary */}
                  <div style={panelCard}>
                    <SectionHeader>AI SIGNAL SUMMARY</SectionHeader>
                    {watchlist.slice(0,4).map(t => {
                      const s = sig[t] || { signal:"HOLD", conf:50, risk:"MEDIUM" };
                      return (
                        <div key={t} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"9px 0", borderBottom:`1px solid ${C.border}` }}>
                          <div>
                            <span style={{ fontSize:14, fontWeight:700, color:C.orange, marginRight:10 }}>{t}</span>
                            <span style={{ fontSize:10, color:C.textMuted }}>{s.risk} RISK</span>
                          </div>
                          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                            <span style={{ fontSize:11, color:C.textSoft }}>{s.conf}%</span>
                            <SigTag sig={s.signal} />
                          </div>
                        </div>
                      );
                    })}
                    <div style={{ fontSize:8, color:C.textFaint, marginTop:10, letterSpacing:"0.05em", lineHeight:1.6 }}>
                      SIGNALS GENERATED BY ARC-AI
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div style={panelCard}>
                    <SectionHeader>SIGNAL RECOMMENDATIONS</SectionHeader>
                    <table style={{ width:"100%", borderCollapse:"collapse" }}>
                      <thead>
                        <tr>{["TICKER","CONF%","ACTION"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                      </thead>
                      <tbody>
                        {RECS.map(r => (
                          <tr key={r.t}>
                            <td style={{ ...td, color:C.orange, fontWeight:700 }}>{r.t}</td>
                            <td style={{ ...td, color:C.green }}>{r.conf}%</td>
                            <td style={td}><SigTag sig={r.act} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}


          {/* ════════════ MARKET DATA ════════════════════════════════════════ */}
          {page === "market" && (
            <div>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
                <SectionHeader>MODULE 1 — LIVE MARKET DATA</SectionHeader>
                <Btn onClick={fetchAll} disabled={Object.values(loading).some(Boolean)}>FETCH ALL LIVE</Btn>
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8, marginBottom:14 }}>
                {watchlist.map(t => (
                  <EtfPanel key={t} d={mkt[t] || { ticker:t, chg:0, price:0 }} s={sig[t]} onRefresh={refreshAll} loading={!!loading.ALL} />
                ))}
              </div>


              {/* Comparison table */}
              <div style={panelCard}>
                <SectionHeader>INDICATOR COMPARISON</SectionHeader>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr>{["TICKER","PRICE","CHG%","RSI(14)","MACD","BB","SMA20","SMA50","VOL","52W HI","52W LO"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {watchlist.map(t => {
                      const d = mkt[t] || { ticker:t, chg:0, price:0, hi52:0, lo52:0, vol:0 };
                      const up = d.chg >= 0;
                      return (
                        <tr key={t}>
                          <td style={{ ...td, color:C.orange, fontWeight:700 }}>{t}</td>
                          <td style={{ ...td, color:C.text, fontWeight:600 }}>${d.price?.toFixed(2)}</td>
                          <td style={{ ...td, color: up ? C.green : C.red, fontWeight:600 }}>{up?"+":""}{d.chg?.toFixed(2)}%</td>
                          <td style={{ ...td, color: d.rsi > 70 ? C.red : d.rsi < 30 ? C.green : C.textSoft }}>{d.rsi?.toFixed(1)}</td>
                          <td style={{ ...td, color: d.macd==="BULLISH"?C.green:d.macd==="BEARISH"?C.red:C.amber }}>{d.macd}</td>
                          <td style={{ ...td, color: d.bb==="OVERBOUGHT"?C.red:d.bb==="OVERSOLD"?C.green:C.textSoft }}>{d.bb}</td>
                          <td style={{ ...td, color: d.sma20==="ABOVE"?C.green:C.red }}>{d.sma20}</td>
                          <td style={{ ...td, color: d.sma50==="ABOVE"?C.green:C.red }}>{d.sma50}</td>
                          <td style={td}>{(d.vol/1e6).toFixed(1)}M</td>
                          <td style={{ ...td, color:C.green }}>${d.hi52}</td>
                          <td style={{ ...td, color:C.red }}>${d.lo52}</td>
                        </tr>
                      );
                    })}
                  </tbody>

                </table>
              </div>
            </div>
          )}

          {/* ════════════ SIGNALS ═════════════════════════════════════════════ */}
          {page === "signals" && (
            <div>
              <SectionHeader>MODULE 2 — AI SIGNAL ANALYSIS</SectionHeader>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8, marginBottom:14 }}>
                {watchlist.map(t => {
                  const s = sig[t] || { signal:"HOLD", conf:50, risk:"MEDIUM", reason:"No signal data" }; 
                  const d = mkt[t] || { ticker:t, name:t };
                  const sigColor = s.signal==="BUY"?C.green:s.signal==="SELL"?C.red:C.amber;
                  return (
                    <div key={t} style={panelCard}>

                      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:10 }}>
                        <div>
                          <div style={{ fontSize:18, fontWeight:700, color:C.orange }}>{t}</div>
                          <div style={{ fontSize:9, color:C.textMuted }}>{d.name}</div>
                        </div>
                        <SigTag sig={s.signal} />
                      </div>
                      <HR my={8} />
                      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6, marginBottom:10 }}>
                        {[
                          ["CONFIDENCE", `${s.conf}%`, sigColor],
                          ["RISK LEVEL", s.risk, C.amber],
                          ["TIMEFRAME", s.tf, C.textSoft],
                          ["STOP LOSS", s.stop ? `$${s.stop.toFixed(2)}` : "N/A", C.red],
                          ...(s.entry ? [["ENTRY", `$${s.entry.toFixed(2)}`, C.green]] : []),
                          ...(s.exit  ? [["EXIT TARGET", `$${s.exit.toFixed(2)}`, C.green]] : []),
                        ].map(([l,v,c]) => (
                          <div key={l}>
                            <div style={{ fontSize:9, color:C.orange, letterSpacing:"0.06em" }}>{l}</div>
                            <div style={{ fontSize:12, fontWeight:600, color:c }}>{v}</div>
                          </div>
                        ))}
                      </div>
                      <HR my={6} />
                      <div style={{ fontSize:10, color:C.textSoft, lineHeight:1.6 }}>{s.reason}</div>
                    </div>
                  );
                })}
              </div>

              {/* Full signal table */}
              <div style={panelCard}>
                <SectionHeader>SIGNAL SUMMARY TABLE</SectionHeader>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr>{["TICKER","SIGNAL","CONF%","RISK","TIMEFRAME","ENTRY","EXIT","STOP"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {watchlist.map(t => {
                      const s = sig[t] || { signal:"HOLD", conf:50, risk:"MEDIUM" };
                      return (
                        <tr key={t}>
                          <td style={{ ...td, color:C.orange, fontWeight:700 }}>{t}</td>
                          <td style={td}><SigTag sig={s.signal} /></td>
                          <td style={{ ...td, color:s.conf>=70?C.green:s.conf>=50?C.amber:C.red, fontWeight:600 }}>{s.conf}%</td>
                          <td style={{ ...td, color:C.amber }}>{s.risk}</td>
                          <td style={td}>{s.tf || "N/A"}</td>
                          <td style={{ ...td, color:C.green }}>{s.entry ? `$${s.entry.toFixed(2)}` : "—"}</td>
                          <td style={{ ...td, color:C.green }}>{s.exit  ? `$${s.exit.toFixed(2)}`  : "—"}</td>
                          <td style={{ ...td, color:C.red   }}>{s.stop  ? `$${s.stop.toFixed(2)}`  : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>

                </table>
              </div>
            </div>
          )}

          {/* ════════════ TRADING ═════════════════════════════════════════════ */}
          {page === "trading" && (
            <div>
              <SectionHeader>MODULE 3 — TRADE EXECUTION</SectionHeader>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>

                {/* Auto-Trade */}
                <div style={panelCard}>
                  <Label>AUTO-TRADING ENGINE</Label>
                  <HR my={8} />
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
                    <div>
                      <div style={{ fontSize:12, color:C.textSoft, marginBottom:4 }}>CURRENT STATUS</div>
                      <div style={{ fontSize:16, fontWeight:700, color:autoTrade ? C.green : C.textMuted }}>{autoStatus}</div>
                    </div>
                    <div style={{ display:"flex", gap:6 }}>
                      <Btn onClick={toggleAutoTrade} primary={!autoTrade} style={{ borderColor: autoTrade ? C.red : C.green, color: autoTrade ? (autoTrade ? "#000" : C.red) : "#000", background: autoTrade ? C.red : C.green }}>
                        {autoTrade ? "DISABLE" : "ENABLE"}
                      </Btn>
                    </div>
                  </div>
                  <HR my={8} />
                  <div style={{ fontSize:9, color:C.textMuted, lineHeight:1.8 }}>
                    <div>STRATEGY: SIGNAL-BASED AUTO-EXECUTION</div>
                    <div>CONFIDENCE THRESHOLD: 70%</div>
                    <div>RISK LIMIT: 2% PER TRADE</div>
                    <div>MAX POSITION: 50% OF ACCOUNT</div>
                    <div>DAILY LOSS LIMIT: 5% HARD STOP</div>
                  </div>
                </div>

                {/* Manual trade */}
                <div style={panelCard}>
                  <Label>MANUAL TRADE ENTRY</Label>
                  <HR my={8} />
                  
                  <div style={{ marginBottom:12 }}>
                    <Label>EXECUTION MODE</Label>
                    <div style={{ display:"flex", gap:4 }}>
                      <button onClick={() => setTradeForm(f => ({ ...f, auto_size:false }))} style={{ flex:1, padding:4, fontSize:9, background: !tradeForm.auto_size ? C.orange : "transparent", color: !tradeForm.auto_size ? "#000" : C.orange, border:`1px solid ${C.orange}`, cursor:"pointer" }}>MANUAL (DIRECT)</button>
                      <button onClick={() => setTradeForm(f => ({ ...f, auto_size:true })) } style={{ flex:1, padding:4, fontSize:9, background: tradeForm.auto_size ? C.orange : "transparent", color: tradeForm.auto_size ? "#000" : C.orange, border:`1px solid ${C.orange}`, cursor:"pointer" }}>SMART (AI ADJUSTED)</button>
                    </div>
                  </div>

                  <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                    <div>
                      <Label>TICKER</Label>
                      <input type="text" value={tradeForm.ticker} onChange={e => setTradeForm(f => ({ ...f, ticker:e.target.value.toUpperCase() }))} style={{ width:"100%" }} />
                    </div>
                    <div>
                      <Label>SIDE</Label>
                      <select value={tradeForm.side} onChange={e => setTradeForm(f => ({ ...f, side:e.target.value }))} style={{ width:"100%" }}>
                        <option>BUY</option>
                        <option>SELL</option>
                      </select>
                    </div>
                    {!tradeForm.auto_size && (
                      <>
                        <div>
                          <Label>QUANTITY</Label>
                          <input type="number" value={tradeForm.qty} onChange={e => setTradeForm(f => ({ ...f, qty:parseInt(e.target.value) }))} style={{ width:"100%" }} />
                        </div>
                        <div>
                          <Label>EST. PRICE</Label>
                          <div style={{ fontSize:14, color:C.textSoft, padding:"5px 0" }}>${mkt[tradeForm.ticker]?.price?.toFixed(2) || "---"}</div>
                        </div>
                      </>
                    )}
                  </div>

                  <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                    <span style={{ fontSize:10, color:C.textSoft }}>
                      {!tradeForm.auto_size ? `TOTAL: $${((tradeForm.qty || 0) * (mkt[tradeForm.ticker]?.price || 0)).toFixed(2)}` : "AUTO-CALCULATED BY AI"}
                    </span>
                    <Btn onClick={submitTrade} primary>SUBMIT ORDER</Btn>
                  </div>
                  {tradeMsg && (
                    <div style={{ marginTop:10, padding:"6px 10px", background:tradeMsg.includes("FILLED")?`${C.green}15`:`${C.red}15`, border:`1px solid ${tradeMsg.includes("FILLED")?C.green:C.red}`, fontSize:10, color:tradeMsg.includes("FILLED")?C.green:C.red }}>
                      {tradeMsg}
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* ════════════ POSITIONS ═══════════════════════════════════════════ */}
          {page === "positions" && (
            <div>
              <SectionHeader>OPEN POSITIONS</SectionHeader>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8, marginBottom:14 }}>
                <StatBox label="PORTFOLIO VALUE"  value={`$${(totalValue + cash).toLocaleString("en-AU",{minimumFractionDigits:2})}`} />
                <StatBox label="EQUITY VALUE"     value={`$${totalValue.toFixed(2)}`} />
                <StatBox label="UNREALISED P&L"    value={`${totalPnL>=0?"+":""}$${totalPnL.toFixed(2)}`} subColor={pnlColor} sub={`${totalPnL>=0?"+":""}${((totalPnL/totalValue)*100).toFixed(2)}%`} />
                <StatBox label="CASH AVAILABLE"   value={`$${cash.toFixed(2)}`} />
              </div>
              <div style={panelCard}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr>{["SYMBOL","QTY","ENTRY PRICE","CURRENT PRICE","MARKET VALUE","UNREAL P&L","RETURN %"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {positions.map(p => {
                      const pnl = p.qty * (p.curr - p.entry);
                      const pnlPct = (pnl / (p.qty * p.entry)) * 100;
                      const col = pnl >= 0 ? C.green : C.red;
                      return (
                        <tr key={p.sym}>
                          <td style={{ ...td, color:C.orange, fontWeight:700 }}>{p.sym}</td>
                          <td style={td}>{p.qty}</td>
                          <td style={td}>${p.entry.toFixed(2)}</td>
                          <td style={{ ...td, color:C.text, fontWeight:600 }}>${p.curr.toFixed(2)}</td>
                          <td style={{ ...td, color:C.text }}>${(p.qty * p.curr).toFixed(2)}</td>
                          <td style={{ ...td, color:col, fontWeight:600 }}>{pnl>=0?"+":""}${pnl.toFixed(2)}</td>
                          <td style={{ ...td, color:col, fontWeight:600 }}>{pnlPct>=0?"+":""}{pnlPct.toFixed(2)}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════ TAX LOG ══════════════════════════════════════════════ */}
          {page === "taxlog" && (
            <div>
              <SectionHeader>TRADE & TAX LOG — ATO COMPLIANT FORMAT</SectionHeader>
              <div style={panelCard}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr>{["DATE","TICKER","ACTION","QTY","PRICE","TOTAL","REASON / SIGNAL"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {taxLog.map((r,i) => (
                      <tr key={i}>
                        <td style={td}>{r.date}</td>
                        <td style={{ ...td, color:C.orange, fontWeight:700 }}>{r.t}</td>
                        <td style={{ ...td, color: r.act==="BUY"?C.green:C.red, fontWeight:700 }}>{r.act}</td>
                        <td style={td}>{r.qty}</td>
                        <td style={td}>${r.px.toFixed(2)}</td>
                        <td style={{ ...td, color:C.text, fontWeight:600 }}>${r.tot.toFixed(2)}</td>
                        <td style={{ ...td, color:C.textMuted, fontSize:10 }}>{r.why}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div style={{ marginTop:12, fontSize:9, color:C.textFaint, letterSpacing:"0.05em" }}>
                  {taxLog.length} RECORDS · PAPER TRADING ACCOUNT · FOR TAX REFERENCE ONLY
                </div>
              </div>
            </div>
          )}

          {/* ════════════ ORDERS ══════════════════════════════════════════════════ */}
          {page === "orders" && (
            <div>
              <SectionHeader>ALPACA ORDER HISTORY</SectionHeader>
              <div style={panelCard}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr>{["ID","TICKER","SIDE","TYPE","QTY","FILLED","PRICE","STATUS","CREATED"].map(h => <th key={h} style={th}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {orders.length === 0 ? (
                      <tr><td colSpan="9" style={{ ...td, textAlign:"center" }}>NO RECENT ORDERS FOUND</td></tr>
                    ) : (
                      orders.map(o => (
                        <tr key={o.id}>
                          <td style={{ ...td, fontSize:9, color:C.textMuted }}>{o.id.slice(0,8)}...</td>
                          <td style={{ ...td, color:C.orange, fontWeight:700 }}>{o.ticker}</td>
                          <td style={{ ...td, color: o.side==="BUY" ? C.green : C.red }}>{o.side}</td>
                          <td style={td}>{o.type.toUpperCase()}</td>
                          <td style={td}>{o.qty}</td>
                          <td style={td}>{o.filled_qty}</td>
                          <td style={td}>{o.filled_avg_price ? `$${o.filled_avg_price.toFixed(2)}` : "—"}</td>
                          <td style={{ ...td, fontWeight:700, color: o.status==="FILLED" ? C.green : o.status==="CANCELED" ? C.red : C.amber }}>{o.status}</td>
                          <td style={td}>{new Date(o.created_at).toLocaleString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}


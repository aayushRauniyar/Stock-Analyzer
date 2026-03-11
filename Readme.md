<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>未来アークスフィア · Mirai ArcSphere</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;700&family=Zen+Old+Mincho:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Shippori+Mincho+B1:wght@400;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --washi:#fdf8f3;--ivory:#faf4ec;--parchment:#f2e8d9;--cream:#ede0cc;
    --blush:#f5c5ce;--sakura:#e8a0b0;--rose:#d4637a;--deep-rose:#b84d63;
    --petal-light:#fde8ed;--petal-mid:#f9d0da;
    --ink:#1a1008;--ink-soft:#3d2d1e;--ink-dim:#7a6555;--ink-faint:#b09e8e;
    --moss:#7a9e7e;--celadon:#a8c5a0;--gold:#c9923a;--gold-light:#e8b86d;
    --border-soft:rgba(212,99,122,0.15);--border-blush:rgba(212,99,122,0.28);
    --shadow:rgba(184,77,99,0.08);
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{background:var(--washi);color:var(--ink-soft);font-family:'Crimson Pro',Georgia,serif;overflow-x:hidden;min-height:100vh;position:relative}
  body::before{content:'';position:fixed;inset:0;background-image:radial-gradient(ellipse at 15% 10%,rgba(245,197,206,.18) 0%,transparent 55%),radial-gradient(ellipse at 85% 85%,rgba(232,160,176,.13) 0%,transparent 50%),radial-gradient(ellipse at 55% 45%,rgba(245,197,206,.07) 0%,transparent 40%);pointer-events:none;z-index:0}
  canvas{position:fixed;inset:0;z-index:1;pointer-events:none}
  .kanji-bg{position:fixed;font-family:'Zen Old Mincho',serif;font-weight:900;pointer-events:none;z-index:2;user-select:none;line-height:1}
  .kb1{font-size:32vw;top:-8%;right:-6%;color:rgba(212,99,122,.04)}
  .kb2{font-size:18vw;bottom:12%;left:-5%;color:rgba(201,146,58,.038)}
  .kb3{font-size:10vw;top:42%;left:7%;color:rgba(122,158,126,.055)}
  .wrapper{position:relative;z-index:10;max-width:980px;margin:0 auto;padding:0 28px 100px}

  /* NAV */
  .nav{position:sticky;top:0;z-index:100;background:rgba(253,248,243,.9);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--border-soft);padding:13px 28px;display:flex;align-items:center;gap:20px}
  .nav-brand{font-family:'Zen Old Mincho',serif;font-size:16px;font-weight:700;color:var(--deep-rose);letter-spacing:.05em;flex-shrink:0}
  .nav-brand em{font-family:'Noto Serif JP',serif;font-size:10px;font-style:normal;color:var(--ink-faint);margin-left:10px;letter-spacing:.15em}
  .nav-links{display:flex;gap:24px;margin-left:auto;list-style:none}
  .nav-links a{font-family:'Shippori Mincho B1',serif;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-faint);text-decoration:none;transition:color .25s;position:relative;padding-bottom:2px}
  .nav-links a::after{content:'';position:absolute;bottom:0;left:0;width:0;height:1px;background:var(--rose);transition:width .3s}
  .nav-links a:hover{color:var(--rose)}
  .nav-links a:hover::after{width:100%}

  /* HERO */
  .hero{padding:88px 0 68px;text-align:center;position:relative}
  .branch-r{position:absolute;top:36px;right:-10px;pointer-events:none;opacity:0;animation:fadeIn 1.2s .4s forwards}
  .hero-mon{width:68px;height:68px;border:1.5px solid var(--blush);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 26px;position:relative;opacity:0;animation:fadeIn .8s .1s forwards}
  .hero-mon::before{content:'';position:absolute;inset:4px;border:1px solid var(--petal-mid);border-radius:50%}
  .hero-mon-inner{font-size:26px}
  .hero-eye{font-family:'Noto Serif JP',serif;font-size:11px;letter-spacing:.38em;color:var(--ink-faint);text-transform:uppercase;margin-bottom:18px;opacity:0;animation:fadeUp .8s .3s forwards}
  .hero-jp{font-family:'Zen Old Mincho',serif;font-weight:900;font-size:clamp(50px,9vw,86px);color:var(--deep-rose);letter-spacing:.12em;line-height:1;text-shadow:0 2px 40px rgba(184,77,99,.12),0 1px 0 rgba(255,255,255,.8);opacity:0;animation:fadeUp .9s .5s forwards;cursor:default;transition:text-shadow .4s}
  .hero-jp:hover{text-shadow:0 2px 60px rgba(184,77,99,.28),2px 0 0 rgba(245,197,206,.5),-2px 0 0 rgba(201,146,58,.3)}
  .hero-title{font-family:'Shippori Mincho B1',serif;font-weight:800;font-size:clamp(16px,3.5vw,26px);color:var(--ink-soft);letter-spacing:.25em;text-transform:uppercase;margin-top:13px;opacity:0;animation:fadeUp .8s .7s forwards}
  .hero-desc{font-family:'Crimson Pro',serif;font-size:16px;font-style:italic;color:var(--ink-dim);letter-spacing:.04em;margin-top:11px;line-height:1.6;opacity:0;animation:fadeUp .8s .9s forwards}
  .pdiv{display:flex;align-items:center;gap:14px;margin:34px auto;max-width:480px;opacity:0;animation:fadeUp .8s 1.1s forwards}
  .pdiv::before,.pdiv::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--blush),transparent)}
  .pdiv-mid{display:flex;gap:10px;align-items:center}
  .pdiv-mid span{font-size:14px;opacity:.65;animation:sway 3s ease-in-out infinite}
  .pdiv-mid span:nth-child(2){animation-delay:.5s;font-size:10px;opacity:.45}
  .pdiv-mid span:nth-child(3){animation-delay:1s}
  @keyframes sway{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}

  /* BADGES */
  .badge-row{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-bottom:20px;opacity:0;animation:fadeUp .8s 1.3s forwards}
  .badge{padding:5px 15px;font-family:'Shippori Mincho B1',serif;font-size:10px;letter-spacing:.14em;text-transform:uppercase;border-radius:20px;border:1px solid;transition:all .3s;cursor:default}
  .badge:hover{transform:translateY(-2px)}
  .b-rose{color:var(--deep-rose);border-color:var(--blush);background:var(--petal-light)}
  .b-gold{color:var(--gold);border-color:rgba(201,146,58,.3);background:rgba(232,184,109,.1)}
  .b-moss{color:var(--moss);border-color:rgba(122,158,126,.3);background:rgba(168,197,160,.1)}
  .b-ink{color:var(--ink-dim);border-color:var(--cream);background:var(--ivory)}

  /* SECTIONS */
  .sec{margin-bottom:62px;opacity:0;transform:translateY(26px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}
  .sec.vis{opacity:1;transform:none}
  .sec-head{display:flex;align-items:flex-end;gap:16px;margin-bottom:26px;padding-bottom:15px;border-bottom:1px solid var(--border-soft);position:relative}
  .sec-head::after{content:'';position:absolute;bottom:-1px;left:0;width:60px;height:2px;background:linear-gradient(90deg,var(--rose),var(--blush));border-radius:2px}
  .sec-jp{font-family:'Noto Serif JP',serif;font-size:11px;color:var(--sakura);writing-mode:vertical-rl;letter-spacing:.2em;line-height:1.4;flex-shrink:0}
  .sec-en{font-family:'Zen Old Mincho',serif;font-size:21px;font-weight:700;color:var(--ink-soft);letter-spacing:.06em}
  .sec-en span{color:var(--rose)}
  .sec-no{margin-left:auto;font-family:'Noto Serif JP',serif;font-size:10px;color:rgba(212,99,122,.28);letter-spacing:.2em;align-self:flex-start;padding-top:3px}

  /* INTRO CARDS */
  .igrid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .icard{background:var(--ivory);border:1px solid var(--border-soft);padding:24px 25px;position:relative;overflow:hidden;transition:border-color .3s,box-shadow .3s}
  .icard:hover{border-color:var(--border-blush);box-shadow:0 8px 30px var(--shadow)}
  .icard::before{content:attr(data-k);position:absolute;bottom:-14px;right:-6px;font-family:'Zen Old Mincho',serif;font-size:78px;font-weight:900;color:rgba(212,99,122,.05);pointer-events:none;line-height:1}
  .ilabel{font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.3em;text-transform:uppercase;color:var(--rose);margin-bottom:9px}
  .itext{font-size:15px;line-height:1.8;color:var(--ink-soft)}
  .ijp{display:block;margin-top:9px;font-family:'Noto Serif JP',serif;font-size:10px;color:var(--ink-faint);letter-spacing:.1em;font-style:italic}

  /* FEATURE GRID */
  .fgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border-soft);border:1px solid var(--border-soft)}
  .fcard{background:var(--washi);padding:25px 21px;position:relative;overflow:hidden;transition:background .3s}
  .fcard:hover{background:var(--ivory)}
  .fcard::after{content:attr(data-k);position:absolute;bottom:-8px;right:-3px;font-family:'Zen Old Mincho',serif;font-size:54px;font-weight:900;color:rgba(212,99,122,.05);pointer-events:none;line-height:1;transition:color .3s}
  .fcard:hover::after{color:rgba(212,99,122,.1)}
  .ficon{font-size:21px;margin-bottom:11px;display:block}
  .fname{font-family:'Shippori Mincho B1',serif;font-size:13px;font-weight:700;color:var(--ink-soft);letter-spacing:.05em;margin-bottom:8px}
  .fdesc{font-size:13px;color:var(--ink-dim);line-height:1.75}
  .ftag{display:inline-block;margin-top:11px;font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.14em;text-transform:uppercase;padding:3px 10px;border:1px solid var(--blush);color:var(--rose);background:var(--petal-light);border-radius:10px}

  /* TABLE */
  .tbl{width:100%;border-collapse:collapse;font-size:13px}
  .tbl thead tr{border-bottom:2px solid var(--blush)}
  .tbl th{padding:10px 15px;text-align:left;font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:var(--rose);font-weight:400;background:var(--petal-light)}
  .tbl td{padding:13px 15px;border-bottom:1px solid rgba(212,99,122,.08);line-height:1.65;vertical-align:top}
  .tbl tr:hover td{background:rgba(245,197,206,.1)}
  .ca{font-family:'Shippori Mincho B1',serif;font-size:14px;font-weight:700;color:var(--ink-soft);letter-spacing:.04em}
  .cb{color:var(--rose);font-size:12px}
  .cc{color:var(--ink-dim);font-size:12px}
  .cn{color:var(--sakura);font-size:11px;font-family:'Noto Serif JP',serif}

  /* CODE */
  .cbox{background:var(--ink);border:1px solid rgba(212,99,122,.2);border-top:3px solid var(--rose);position:relative;overflow:hidden;margin-bottom:16px}
  .clabel{position:absolute;top:0;right:0;padding:4px 14px;background:rgba(212,99,122,.15);font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.2em;color:var(--sakura);text-transform:uppercase}
  .cbox pre{padding:22px 22px 18px;overflow-x:auto;font-family:monospace;font-size:13px;line-height:1.9;color:#c8bfb0}
  .cm{color:#6b5e50}.ck{color:var(--sakura)}.cs{color:var(--blush)}.cv{color:var(--gold-light)}.cg{color:var(--celadon)}

  /* FILE TREE */
  .ftree{background:var(--ivory);border:1px solid var(--border-soft);border-left:3px solid var(--blush);padding:20px 24px;font-family:monospace;font-size:13px;line-height:2.1}
  .ftd{color:var(--rose);font-weight:600}.fth{color:var(--deep-rose)}.ftf{color:var(--ink-soft)}.ftn{color:var(--ink-faint);font-style:italic}

  /* INFO BOX */
  .ibox{display:grid;grid-template-columns:52px 1fr;border:1px solid var(--border-soft);margin-bottom:12px;overflow:hidden;transition:border-color .3s}
  .ibox:hover{border-color:var(--border-blush)}
  .ib-i{display:flex;align-items:center;justify-content:center;font-size:18px;border-right:1px solid var(--border-soft)}
  .ib-b{padding:14px 18px}
  .ib-l{font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.25em;text-transform:uppercase;margin-bottom:6px}
  .ib-t{font-size:13px;color:var(--ink-soft);line-height:1.75}
  .ibox.ir .ib-i{background:var(--petal-light)}.ibox.ir .ib-l{color:var(--rose)}
  .ibox.ig .ib-i{background:rgba(232,184,109,.12)}.ibox.ig .ib-l{color:var(--gold)}
  .ibox.im .ib-i{background:rgba(168,197,160,.15)}.ibox.im .ib-l{color:var(--moss)}

  /* STEPS */
  .slist{list-style:none}
  .slist li{display:grid;grid-template-columns:55px 1fr;border-bottom:1px solid rgba(212,99,122,.08);transition:background .2s}
  .slist li:hover{background:rgba(245,197,206,.1)}
  .sno{padding:18px 12px;display:flex;align-items:flex-start;justify-content:center;font-family:'Zen Old Mincho',serif;font-size:12px;color:var(--rose);letter-spacing:.1em;padding-top:20px;border-right:1px solid rgba(212,99,122,.08)}
  .sbody{padding:17px 20px}
  .sbody strong{display:block;font-family:'Shippori Mincho B1',serif;font-size:14px;font-weight:700;color:var(--ink-soft);margin-bottom:5px;letter-spacing:.04em}
  .sbody span{font-size:13px;color:var(--ink-dim);line-height:1.7}

  /* ROADMAP */
  .rmgrid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(212,99,122,.1);border:1px solid var(--border-soft)}
  .rmitem{background:var(--washi);padding:18px 20px;display:flex;gap:14px;align-items:flex-start;transition:background .3s}
  .rmitem:hover{background:var(--ivory)}
  .rmdot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px}
  .rmd-done{background:var(--rose);box-shadow:0 0 8px rgba(212,99,122,.5)}
  .rmd-soon{background:var(--gold);box-shadow:0 0 8px rgba(201,146,58,.4)}
  .rmd-future{background:var(--cream);border:1px solid var(--ink-faint)}
  .rmst{font-family:'Shippori Mincho B1',serif;font-size:9px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:4px}
  .rmst-done{color:var(--rose)}.rmst-soon{color:var(--gold)}.rmst-future{color:var(--ink-faint)}
  .rmtxt{font-size:13px;color:var(--ink-soft);line-height:1.6}

  /* DISCLAIMER */
  .disc{background:var(--petal-light);border:1px solid var(--blush);padding:24px 28px;position:relative;overflow:hidden}
  .disc::before{content:'警告';position:absolute;right:-8px;top:-10px;font-family:'Zen Old Mincho',serif;font-size:90px;font-weight:900;color:rgba(212,99,122,.06);pointer-events:none;line-height:1}
  .disc-t{font-family:'Shippori Mincho B1',serif;font-size:13px;font-weight:700;color:var(--deep-rose);letter-spacing:.1em;margin-bottom:10px}
  .disc-b{font-size:13px;color:var(--ink-dim);line-height:1.9}

  /* FOOTER */
  .footer{margin-top:80px;padding:46px 0 22px;border-top:1px solid var(--border-soft);text-align:center}
  .f-k{font-family:'Zen Old Mincho',serif;font-size:26px;font-weight:900;color:rgba(212,99,122,.12);letter-spacing:.4em;margin-bottom:10px}
  .f-p{font-size:18px;letter-spacing:12px;color:var(--blush);margin-bottom:14px;opacity:.65}
  .f-t{font-family:'Crimson Pro',serif;font-size:14px;font-style:italic;color:var(--ink-faint);line-height:2.2}
  .f-t a{color:var(--rose);text-decoration:none;transition:color .2s}
  .f-t a:hover{color:var(--deep-rose)}

  /* PETALS CSS */
  .petal{position:fixed;pointer-events:none;z-index:3;animation:petalFall linear infinite}
  @keyframes petalFall{0%{opacity:0;transform:translateY(-30px) rotate(0deg) translateX(0)}8%{opacity:.85}85%{opacity:.55}100%{opacity:0;transform:translateY(108vh) rotate(520deg) translateX(70px)}}

  /* ANIMATIONS */
  @keyframes fadeUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
  @keyframes fadeIn{from{opacity:0}to{opacity:1}}

  @media(max-width:680px){.fgrid{grid-template-columns:1fr}.igrid{grid-template-columns:1fr}.rmgrid{grid-template-columns:1fr}.nav-links{display:none}}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="kanji-bg kb1">桜</div>
<div class="kanji-bg kb2">未来</div>
<div class="kanji-bg kb3">花</div>

<nav class="nav">
  <div class="nav-brand">Mirai ArcSphere <em>未来アークスフィア</em></div>
  <ul class="nav-links">
    <li><a href="#about">About</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#setup">Setup</a></li>
    <li><a href="#legal">Legal</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
  </ul>
</nav>

<div class="wrapper">
  <header class="hero">
    <svg class="branch-r" width="190" height="250" viewBox="0 0 190 250" fill="none">
      <path d="M155 235 C135 195 115 155 95 115 C75 75 55 45 35 18" stroke="#e8a0b0" stroke-width="1.5" fill="none" opacity=".4"/>
      <path d="M95 115 C115 105 135 90 155 75" stroke="#e8a0b0" stroke-width="1" fill="none" opacity=".28"/>
      <path d="M125 165 C143 150 160 134 173 114" stroke="#e8a0b0" stroke-width="1" fill="none" opacity=".22"/>
      <circle cx="35" cy="18" r="5" fill="#f5c5ce" opacity=".65"/><circle cx="37" cy="12" r="3" fill="#f9d0da" opacity=".5"/><circle cx="43" cy="20" r="4" fill="#f5c5ce" opacity=".5"/>
      <circle cx="155" cy="75" r="4" fill="#f9d0da" opacity=".5"/><circle cx="173" cy="114" r="5" fill="#f5c5ce" opacity=".6"/><circle cx="160" cy="134" r="3" fill="#f9d0da" opacity=".4"/>
      <circle cx="95" cy="115" r="3" fill="#e8a0b0" opacity=".4"/>
    </svg>
    <div class="hero-mon"><div class="hero-mon-inner">🌸</div></div>
    <p class="hero-eye">⛩ The Future Blooms · 未来は今ここに咲く</p>
    <h1 class="hero-jp">未来弧</h1>
    <h2 class="hero-title">Mirai ArcSphere</h2>
    <p class="hero-desc">AI-Powered ETF Trading Assistant · Alpaca Markets · Claude AI · Adelaide, Australia</p>
    <div class="pdiv"><div class="pdiv-mid"><span>🌸</span><span>❀</span><span>🌸</span></div></div>
    <div class="badge-row">
      <span class="badge b-rose">Python 3.10+</span>
      <span class="badge b-rose">Alpaca Markets</span>
      <span class="badge b-gold">Claude AI</span>
      <span class="badge b-moss">ASIC Compliant</span>
      <span class="badge b-rose">ATO Tax Logger</span>
      <span class="badge b-ink">Paper Trading</span>
      <span class="badge b-ink">MIT License</span>
      <span class="badge b-ink">Adelaide · Australia</span>
    </div>
  </header>

  <!-- ABOUT -->
  <section class="sec" id="about">
    <div class="sec-head">
      <div class="sec-jp">このプロジェクト</div>
      <h2 class="sec-en">About <span>このプロジェクト</span></h2>
      <div class="sec-no">01 ——</div>
    </div>
    <div class="igrid">
      <div class="icard" data-k="知">
        <div class="ilabel">What It Does</div>
        <div class="itext">Mirai ArcSphere is an open-source AI-powered ETF trading assistant that monitors SPY, QQQ, and VTI. It generates intelligent buy/sell signals, executes automated trades via Alpaca, and maintains a full tax audit trail for Australian compliance.<span class="ijp">AIを活用した自動ETF取引アシスタントです。未来への投資を、賢く。</span></div>
      </div>
      <div class="icard" data-k="旅">
        <div class="ilabel">Who It's For</div>
        <div class="itext">Built by an international student in Adelaide, Australia. Designed for personal algorithmic trading with Australian tax law (ATO) and ASIC regulations built in from day one. Paper trading by default — zero real risk while learning.<span class="ijp">アデレードの国際学生が構築。ATO・ASIC準拠設計。桜のように美しく。</span></div>
      </div>
    </div>
  </section>

  <!-- FEATURES -->
  <section class="sec" id="features">
    <div class="sec-head">
      <div class="sec-jp">機能</div>
      <h2 class="sec-en">Features <span>主な機能</span></h2>
      <div class="sec-no">02 ——</div>
    </div>
    <div class="fgrid">
      <div class="fcard" data-k="知"><span class="ficon">🤖</span><div class="fname">AI Insights Engine</div><div class="fdesc">Claude analyses RSI, MACD, and Bollinger Bands — returning BUY/SELL/HOLD signals with confidence percentage and detailed risk assessment.</div><span class="ftag">Anthropic Claude</span></div>
      <div class="fcard" data-k="取"><span class="ficon">⚡</span><div class="fname">Auto Trade Execution</div><div class="fdesc">Executes market orders on Alpaca when AI confidence reaches 70% or above. Watches SPY, QQQ, VTI every 60 minutes on autopilot.</div><span class="ftag">Alpaca API</span></div>
      <div class="fcard" data-k="守"><span class="ficon">🛡</span><div class="fname">Risk Management</div><div class="fdesc">Stop-loss at 3%, daily loss limit at 5%, maximum 2% account risk per trade. Automated kill-switch protection built in.</div><span class="ftag">ASIC Compliant</span></div>
      <div class="fcard" data-k="税"><span class="ficon">🧾</span><div class="fname">ATO Tax Logger</div><div class="fdesc">Every trade auto-saved to CSV with date, price, quantity, and AI reasoning — ready for your Australian tax return each July.</div><span class="ftag">ATO Ready</span></div>
      <div class="fcard" data-k="視"><span class="ficon">📊</span><div class="fname">Live Dashboard</div><div class="fdesc">React dashboard with Portfolio overview, AI Insights per ETF, open Positions, and full Tax Log — all in one elegant view.</div><span class="ftag">React + Tailwind</span></div>
      <div class="fcard" data-k="紙"><span class="ficon">🌸</span><div class="fname">Paper Trading Mode</div><div class="fdesc">Defaults to Alpaca paper trading — virtual money on real market prices. Zero financial risk while you build confidence and strategy.</div><span class="ftag">Zero Risk</span></div>
    </div>
  </section>

  <!-- TECH STACK -->
  <section class="sec">
    <div class="sec-head">
      <div class="sec-jp">技術スタック</div>
      <h2 class="sec-en">Tech Stack <span>技術</span></h2>
      <div class="sec-no">03 ——</div>
    </div>
    <table class="tbl">
      <thead><tr><th>Layer</th><th>Technology</th><th>Purpose</th></tr></thead>
      <tbody>
        <tr><td class="ca">Broker</td><td class="cb">Alpaca Markets</td><td class="cc">Paper/live trading, portfolio data, order execution</td></tr>
        <tr><td class="ca">AI Engine</td><td class="cb">Anthropic Claude</td><td class="cc">Market signal generation, reasoning, risk analysis</td></tr>
        <tr><td class="ca">Market Data</td><td class="cb">yfinance</td><td class="cc">60-day historical OHLCV data for all ETFs</td></tr>
        <tr><td class="ca">Indicators</td><td class="cb">ta (Technical Analysis)</td><td class="cc">RSI, MACD, Bollinger Bands, SMA 20/50</td></tr>
        <tr><td class="ca">Dashboard</td><td class="cb">React + Tailwind CSS</td><td class="cc">Live monitoring with 4 functional tabs</td></tr>
        <tr><td class="ca">Data</td><td class="cb">pandas + numpy</td><td class="cc">DataFrame manipulation and numerical analysis</td></tr>
        <tr><td class="ca">Tax Logging</td><td class="cb">Python csv module</td><td class="cc">ATO-compliant trade record keeping</td></tr>
      </tbody>
    </table>
  </section>

  <!-- SETUP -->
  <section class="sec" id="setup">
    <div class="sec-head">
      <div class="sec-jp">設定</div>
      <h2 class="sec-en">Quick Start <span>はじめに</span></h2>
      <div class="sec-no">04 ——</div>
    </div>
    <ol class="slist">
      <li><div class="sno">一</div><div class="sbody"><strong>Get Your Alpaca API Keys (Free)</strong><span>Sign up at alpaca.markets → Paper Trading → API Keys → Generate New Key. Copy your API Key and Secret Key.</span></div></li>
      <li><div class="sno">二</div><div class="sbody"><strong>Get Your Anthropic API Key</strong><span>Sign up at console.anthropic.com → API Keys → Create Key → Add ~$5 USD credits. Enough to run the bot for months.</span></div></li>
      <li><div class="sno">三</div><div class="sbody"><strong>Clone & Install Dependencies</strong><span>Clone the repository and install all Python libraries using the requirements file in one command.</span></div></li>
      <li><div class="sno">四</div><div class="sbody"><strong>Configure Your API Keys</strong><span>Open bot.py and paste your three API keys into the config section at the very top of the file.</span></div></li>
      <li><div class="sno">五</div><div class="sbody"><strong>Launch the Bot 🌸</strong><span>Run python bot.py — the bot immediately begins analysing ETFs and will trade on your Alpaca paper account.</span></div></li>
    </ol>
    <br>
    <div class="cbox"><div class="clabel">TERMINAL</div>
    <pre><span class="cm"># Clone the repository</span>
<span class="cg">git clone</span> https://github.com/yourusername/mirai-arcsphere.git
<span class="cm">cd mirai-arcsphere</span>

<span class="cm"># Install Python dependencies</span>
<span class="cg">pip install</span> -r requirements.txt

<span class="cm"># Configure API keys in bot.py</span>
<span class="cv">ALPACA_API_KEY</span>    = <span class="cs">"YOUR_ALPACA_API_KEY"</span>
<span class="cv">ALPACA_SECRET_KEY</span> = <span class="cs">"YOUR_ALPACA_SECRET_KEY"</span>
<span class="cv">ANTHROPIC_API_KEY</span> = <span class="cs">"YOUR_ANTHROPIC_API_KEY"</span>

<span class="cm"># Launch 🌸</span>
<span class="cg">python bot.py</span>
<span class="cm"># 🌸 Mirai ArcSphere · Paper Trading Mode Active</span>
<span class="cm"># 👁  Watching: SPY · QQQ · VTI</span>
<span class="cm"># 🤖 SPY → BUY (74% confidence) · Executing...</span></pre></div>
    <div class="ftree">
      <div class="ftd">mirai-arcsphere/</div>
      <div>├── <span class="fth">bot.py</span>               <span class="ftn">← Main trading bot — run this first</span></div>
      <div>├── <span class="fth">dashboard.jsx</span>        <span class="ftn">← React live monitoring dashboard</span></div>
      <div>├── <span class="ftf">requirements.txt</span>     <span class="ftn">← Python dependencies</span></div>
      <div>├── <span class="ftf">README.md</span>            <span class="ftn">← Project documentation</span></div>
      <div>└── <span class="ftn">tax_trade_log.csv     ← Auto-created on first trade · ATO record</span></div>
    </div>
  </section>

  <!-- HOW IT WORKS -->
  <section class="sec">
    <div class="sec-head">
      <div class="sec-jp">仕組み</div>
      <h2 class="sec-en">How It Works <span>仕組み</span></h2>
      <div class="sec-no">05 ——</div>
    </div>
    <table class="tbl">
      <thead><tr><th>Phase</th><th>Step</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td class="cn">一</td><td class="ca">Fetch Data</td><td class="cc">Downloads 60 days of OHLCV price history for SPY, QQQ, VTI via yfinance</td></tr>
        <tr><td class="cn">二</td><td class="ca">Indicators</td><td class="cc">Calculates RSI-14, MACD, SMA 20/50, Bollinger Bands automatically in pandas</td></tr>
        <tr><td class="cn">三</td><td class="ca">AI Analysis</td><td class="cc">Sends structured data to Claude API — receives signal, confidence %, reasoning, key risks</td></tr>
        <tr><td class="cn">四</td><td class="ca">Decision Gate</td><td class="cc">Only executes if confidence ≥ 70% AND daily loss limit has not been triggered today</td></tr>
        <tr><td class="cn">五</td><td class="ca">Execute Order</td><td class="cc">Places market buy/sell order via Alpaca REST API on paper or live account</td></tr>
        <tr><td class="cn">六</td><td class="ca">Log Trade</td><td class="cc">Instantly appends full trade details to tax_trade_log.csv for ATO compliance</td></tr>
        <tr><td class="cn">七</td><td class="ca">Stop-Loss</td><td class="cc">Scans all open positions — automatically closes any position that has dropped 3%+</td></tr>
        <tr><td class="cn">八</td><td class="ca">Wait & Repeat</td><td class="cc">Sleeps 60 minutes then starts the full cycle again, continuously</td></tr>
      </tbody>
    </table>
  </section>

  <!-- LEGAL -->
  <section class="sec" id="legal">
    <div class="sec-head">
      <div class="sec-jp">法律</div>
      <h2 class="sec-en">Legal & Tax <span>オーストラリア法令</span></h2>
      <div class="sec-no">06 ——</div>
    </div>
    <div class="ibox ir"><div class="ib-i">⚖</div><div class="ib-b"><div class="ib-l">ASIC — Personal Use Only</div><div class="ib-t">This bot is for personal trading only. Offering it as a service to others requires an Australian Financial Services Licence (AFSL). No AFSL is needed for personal use.</div></div></div>
    <div class="ibox ig"><div class="ib-i">🧾</div><div class="ib-b"><div class="ib-l">ATO — International Students (Temporary Residents)</div><div class="ib-t">Alpaca is a US broker — profits may qualify as foreign income and be exempt from Australian tax for temporary residents on student visas. Always confirm with a registered tax agent. Lodge your return annually July 1 – Oct 31.</div></div></div>
    <div class="ibox im"><div class="ib-i">📋</div><div class="ib-b"><div class="ib-l">Tax File Number (TFN) Required</div><div class="ib-t">Apply for a TFN at ato.gov.au (free, ~10 minutes). Required to open a brokerage account in Australia. Use the ATO's free Tax Help Programme if earning under $70,000 AUD.</div></div></div>
  </section>

  <!-- ROADMAP -->
  <section class="sec" id="roadmap">
    <div class="sec-head">
      <div class="sec-jp">未来</div>
      <h2 class="sec-en">Roadmap <span>ロードマップ</span></h2>
      <div class="sec-no">07 ——</div>
    </div>
    <div class="rmgrid">
      <div class="rmitem"><div class="rmdot rmd-done"></div><div><div class="rmst rmst-done">Complete</div><div class="rmtxt">Core bot: Alpaca + Claude integration, ETF trading, stop-loss, tax logger</div></div></div>
      <div class="rmitem"><div class="rmdot rmd-done"></div><div><div class="rmst rmst-done">Complete</div><div class="rmtxt">React dashboard with Portfolio, AI Insights, Positions, Tax Log tabs</div></div></div>
      <div class="rmitem"><div class="rmdot rmd-soon"></div><div><div class="rmst rmst-soon">Coming Soon</div><div class="rmtxt">Email and SMS alerts when trades are placed or stop-loss triggers</div></div></div>
      <div class="rmitem"><div class="rmdot rmd-soon"></div><div><div class="rmst rmst-soon">Coming Soon</div><div class="rmtxt">Backtesting module — test strategies on historical price data</div></div></div>
      <div class="rmitem"><div class="rmdot rmd-future"></div><div><div class="rmst rmst-future">Future</div><div class="rmtxt">News sentiment analysis integrated into the AI signal pipeline</div></div></div>
      <div class="rmitem"><div class="rmdot rmd-future"></div><div><div class="rmst rmst-future">Future</div><div class="rmtxt">Sharesight API integration for automatic ATO tax report export</div></div></div>
    </div>
  </section>

  <!-- DISCLAIMER -->
  <section class="sec">
    <div class="disc">
      <div class="disc-t">⚠ 免責事項 · Disclaimer</div>
      <div class="disc-b">This project is for educational and personal use only. It is <strong>not financial advice</strong>. Past performance does not guarantee future results.<br>Always begin with paper trading. Never invest money you cannot afford to lose. Consult a registered financial advisor and ATO-registered tax agent before live trading.<br><br><em>このプロジェクトは教育・個人利用のみを目的としています。投資アドバイスではありません。桜の花びらのように、リスクは軽やかに管理しましょう。</em></div>
    </div>
  </section>

  <footer class="footer">
    <div class="f-p">🌸 ❀ 🌸 ❀ 🌸</div>
    <div class="f-k">未来弧 ◈ 桜</div>
    <div class="f-t">Built with 🌸 in Adelaide, Australia<br>Powered by <a href="https://alpaca.markets">Alpaca Markets</a> · <a href="https://anthropic.com">Anthropic Claude</a><br>MIT License · © 2025 Mirai ArcSphere</div>
  </footer>
</div>

<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let W,H;
function resize(){W=canvas.width=innerWidth;H=canvas.height=innerHeight}
resize();window.addEventListener('resize',resize);
const nodes=Array.from({length:50},()=>({x:Math.random()*1400,y:Math.random()*900,vx:(Math.random()-.5)*.18,vy:(Math.random()-.5)*.18,r:Math.random()*1.2+.4,a:Math.random()*.2+.05,c:Math.random()>.6?[232,160,176]:Math.random()>.5?[212,99,122]:[201,146,58]}));
function draw(){ctx.clearRect(0,0,W,H);nodes.forEach(n=>{n.x+=n.vx;n.y+=n.vy;if(n.x<0||n.x>W)n.vx*=-1;if(n.y<0||n.y>H)n.vy*=-1;ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fillStyle=`rgba(${n.c[0]},${n.c[1]},${n.c[2]},${n.a})`;ctx.fill()});for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y,d=Math.hypot(dx,dy);if(d<88){ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.strokeStyle=`rgba(232,160,176,${(1-d/88)*.055})`;ctx.lineWidth=.5;ctx.stroke()}}requestAnimationFrame(draw)}
draw();

// Falling petals
const pc=[['#f9d0da','#f5c5ce'],['#f5c5ce','#e8a0b0'],['#fde8ed','#f9d0da'],['#e8a0b0','#d4637a']];
function spawnPetal(){const el=document.createElement('div');el.className='petal';const sz=Math.random()*7+5,[b1,b2]=pc[Math.floor(Math.random()*pc.length)],dur=Math.random()*9+7,delay=Math.random()*2.5;el.style.cssText=`left:${Math.random()*110-5}vw;top:-20px;width:${sz}px;height:${sz}px;background:radial-gradient(circle at 30% 30%,${b1},${b2});border-radius:${Math.random()>.5?'50% 0 50% 0':'0 50% 0 50%'};animation-duration:${dur}s;animation-delay:${delay}s;opacity:.75;`;document.body.appendChild(el);setTimeout(()=>el.remove(),(dur+delay+1)*1000)}
for(let i=0;i<14;i++)setTimeout(spawnPetal,i*380);
setInterval(spawnPetal,680);

// Cursor petal trail
document.addEventListener('mousemove',e=>{const d=document.createElement('div'),s=Math.random()*5+2;d.style.cssText=`position:fixed;pointer-events:none;z-index:9999;left:${e.clientX}px;top:${e.clientY}px;width:${s}px;height:${s}px;border-radius:${Math.random()>.5?'50% 0 50% 0':'0 50% 0 50%'};background:rgba(212,99,122,${Math.random()*.3+.12});transform:translate(-50%,-50%) rotate(${Math.random()*360}deg);transition:opacity .45s,transform .45s;`;document.body.appendChild(d);requestAnimationFrame(()=>{d.style.opacity='0';d.style.transform+=' scale(0)'});setTimeout(()=>d.remove(),450)});

// Scroll reveal
const obs=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('vis');obs.unobserve(e.target)}})},{threshold:.07});
document.querySelectorAll('.sec').forEach(s=>obs.observe(s));
</script>
</body>
</html>
const REPORT_URL = "https://raw.githubusercontent.com/Sid404-lab/crypto-intelligence-agent/main/data/latest-report.json";
const REPORT_FALLBACK_URL = "/data/latest-report.json";

const els = {
  updatedAt: document.getElementById("updated-at"),
  updatedRelative: document.getElementById("updated-relative"),
  liveClock: document.getElementById("live-clock"),
  paperBalance: document.getElementById("paper-balance"),
  paperReset: document.getElementById("paper-reset"),
  positionsBody: document.getElementById("positions-body"),
  accountEquity: document.getElementById("account-equity"),
  accountCash: document.getElementById("account-cash"),
  accountOpen: document.getElementById("account-open"),
  accountToday: document.getElementById("account-today"),
  journalBody: document.getElementById("journal-body"),
  journalStats: document.getElementById("journal-stats"),
  ordersBody: document.getElementById("orders-body"),
  tradeModal: document.getElementById("trade-modal"),
  tradeClose: document.getElementById("trade-close"),
  tradeSymbol: document.getElementById("trade-symbol"),
  tradeLong: document.getElementById("trade-long"),
  tradeShort: document.getElementById("trade-short"),
  tradePrice: document.getElementById("trade-price"),
  tradeAmount: document.getElementById("trade-amount"),
  tradeQty: document.getElementById("trade-qty"),
  tradeError: document.getElementById("trade-error"),
  tradePlace: document.getElementById("trade-place"),
  tradeToast: document.getElementById("trade-toast"),
  news: document.getElementById("news-list"),
  listings: document.getElementById("listings-body"),
  search: document.getElementById("search"),
  status: document.getElementById("status"),
  scannerBody: document.getElementById("scanner-body"),
  refreshBtn: document.getElementById("refresh-btn"),
  chartContainer: document.getElementById("tradingview-widget"),
  chartControls: document.getElementById("chart-controls"),
  candleCountdown: document.getElementById("candle-countdown"),
  errorBanner: document.getElementById("error-banner"),
  aiMorningSummary: document.getElementById("ai-morning-summary"),
  aiWatchList: document.getElementById("ai-watch-list"),
  marketSentiment: document.getElementById("market-sentiment"),
  sidebar: document.getElementById("sidebar"),
  hamburger: document.getElementById("hamburger"),
  mobileOverlay: document.getElementById("mobile-overlay"),
  sidebarToggle: document.getElementById("sidebar-toggle"),
  comingSoonModal: document.getElementById("coming-soon-modal"),
  comingSoonClose: document.getElementById("coming-soon-close"),
  comingSoonMessage: document.getElementById("coming-soon-message"),
  comingSoonTitle: document.getElementById("coming-soon-title"),
  scrollToNews: document.getElementById("scroll-to-news"),
  aiTabs: document.querySelectorAll(".ai-panel .ai-tab"),
  aiTabPanels: document.querySelectorAll(".ai-panel .ai-tab-panel"),
  aiFullTabs: document.querySelectorAll(".ai-full-panel .ai-tab"),
  aiFullPanels: document.querySelectorAll(".ai-full-panel .ai-tab-panel"),
  aiFullMorningSummary: document.getElementById("ai-full-morning-summary"),
  aiFullMarketSentiment: document.getElementById("ai-full-market-sentiment"),
  aiFullWatchList: document.getElementById("ai-full-watch-list"),
  navItems: document.querySelectorAll(".nav-item[data-view]"),
  topSetupContent: document.getElementById("top-setup-content"),
  setupBody: document.getElementById("setup-body"),
  riskSummary: document.getElementById("risk-summary"),
  riskBody: document.getElementById("risk-body"),
  aiSetupContent: document.getElementById("ai-setup-content"),
  aiRiskContent: document.getElementById("ai-risk-content"),
  aiFullSetupContent: document.getElementById("ai-full-setup-content"),
  aiFullRiskContent: document.getElementById("ai-full-risk-content"),
  aiFullScrollToNews: document.getElementById("ai-full-scroll-to-news"),
  newTrendingBody: document.getElementById("new-trending-body"),
  timezoneSelect: document.getElementById("timezone-select"),
  themeToggle: document.getElementById("theme-toggle"),
  marketsBtn: document.getElementById("markets-btn"),
  marketsDropdown: document.getElementById("markets-dropdown"),
  mdCats: document.querySelectorAll(".md-cat"),
  mdCFilters: document.querySelectorAll("#markets-dropdown [data-cfilter]"),
  mdSearch: document.getElementById("md-search"),
  mdList: document.getElementById("md-list"),
  mdCount: document.getElementById("md-count"),
  snapTabs: document.querySelectorAll(".snap-tab"),
  snapFilters: document.querySelectorAll("[data-snapfilter]"),
  snapSearch: document.getElementById("snap-search"),
  snapList: document.getElementById("snap-list"),
  snapCount: document.getElementById("snap-count"),
  assetModal: document.getElementById("asset-modal"),
  assetClose: document.getElementById("asset-close"),
  assetBody: document.getElementById("asset-body"),
  assetChartBtn: document.getElementById("asset-chart-btn"),
  assetNoChart: document.getElementById("asset-no-chart"),
  settingsTimezone: document.getElementById("settings-timezone"),
  settingsThemeToggle: document.getElementById("settings-theme-toggle"),
  settingsThemeLabel: document.getElementById("settings-theme-label"),
  settingsBalance: document.getElementById("settings-balance"),
  settingsPositions: document.getElementById("settings-positions"),
  settingsEquity: document.getElementById("settings-equity"),
  settingsReset: document.getElementById("settings-reset"),
  settingsWatchlist: document.getElementById("settings-watchlist"),
};

let report = null;
let activeFilter = "All";
let currentChartSymbol = "BTCUSD";
let currentTimeframe = 60; // minutes: 1, 30, 60
let countdownTimer = null;
let isLoading = false;
let reportTimer = null;
let activeView = "dashboard";

// Markets dropdown state
const METAL_SYMBOLS = ["XAU", "XAG", "PLAT"];
const MD_TOP_N = 20;
const LARGE_CAP_MIN = 10000000000;
let mdOpen = false;
let mdCat = "crypto";
let mdCryptoFilter = "all";
let mdQuery = "";
let mdLastRows = [];

// Inline snapshot panel state (mirrors the dropdown above)
let snapCat = "crypto";
let snapFilter = "all";
let snapQuery = "";
let snapLastRows = [];

const TIMEZONES = {
  IST: "Asia/Kolkata",
  UTC: "UTC",
  EST: "America/New_York",
  GMT: "Etc/GMT",
};

let activeTimezone = "IST";
try {
  const savedTz = localStorage.getItem("pulse-timezone");
  if (savedTz && TIMEZONES[savedTz]) activeTimezone = savedTz;
} catch (err) {
  // localStorage unavailable — fall back to IST default
}

let activeTheme = "dark";
try {
  const savedTheme = localStorage.getItem("pulse-theme");
  if (savedTheme === "light" || savedTheme === "dark") activeTheme = savedTheme;
} catch (err) {
  // localStorage unavailable — fall back to dark default
}

const WATCHLIST = [
  { symbol: "BTC", name: "Bitcoin" },
  { symbol: "ETH", name: "Ethereum" },
  { symbol: "SOL", name: "Solana" },
  { symbol: "BNB", name: "BNB" },
  { symbol: "XRP", name: "XRP" },
  { symbol: "DOGE", name: "Dogecoin" },
];

function formatUsd(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 10000 ? 0 : 2,
    minimumFractionDigits: value >= 10000 ? 0 : 2,
  }).format(value);
}

function formatCompact(value) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatTime(iso) {
  const date = new Date(iso);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: TIMEZONES[activeTimezone] || "Asia/Kolkata",
    timeZoneName: "short",
  }).format(date);
}

function refreshTimestamps() {
  if (!report) return;
  els.updatedAt.textContent = formatTime(report.generated_at);
  renderNews();
}

function formatClock(date) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: TIMEZONES[activeTimezone] || "Asia/Kolkata",
    timeZoneName: "short",
  }).format(date || new Date());
}

function tickClock() {
  if (els.liveClock) els.liveClock.textContent = formatClock(new Date());
}

// ---- Paper trading account (E1 foundation; orders/positions land in E2/E3) ----
const PAPER_KEY = "pulse_paper_account";
const PAPER_DEFAULT_CASH = 10000;

function defaultPaperAccount(now) {
  return {
    version: 1,
    cash: PAPER_DEFAULT_CASH,
    // positions: open trades, each {id, symbol, side ("LONG"/"SHORT"),
    // qty, notionalUsd, entryPrice, openedAt}.
    positions: [],
    // closed: settled trades, each a position plus {exitPrice, realizedPnl,
    // closedAt}. Read by the Trading Journal in E4.
    closed: [],
    createdAt: now,
    updatedAt: now,
  };
}

function loadPaperAccount() {
  try {
    const raw = localStorage.getItem(PAPER_KEY);
    if (!raw) return null;
    const acct = JSON.parse(raw);
    if (!acct || typeof acct.cash !== "number" || !isFinite(acct.cash)) return null;
    if (!Array.isArray(acct.positions)) return null;
    if (!Array.isArray(acct.closed)) acct.closed = [];
    return acct;
  } catch (err) {
    return null;
  }
}

function savePaperAccount(acct) {
  acct.updatedAt = new Date().toISOString();
  try {
    localStorage.setItem(PAPER_KEY, JSON.stringify(acct));
  } catch (err) {
    // localStorage unavailable — account lives in memory for this session
  }
  return acct;
}

function getPaperAccount() {
  const existing = loadPaperAccount();
  if (existing) return existing;
  return savePaperAccount(defaultPaperAccount(new Date().toISOString()));
}

function renderPaperBalance() {
  if (!els.paperBalance) return;
  const acct = getPaperAccount();
  const equity = acct.cash + accountUnrealized(acct);
  els.paperBalance.textContent = formatUsd(equity);
  renderAccountPanel();
  renderSettings();
}

function accountTodayPnl(acct, now) {
  // Realized P&L closed on the local calendar day + current unrealized.
  const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const realizedToday = (acct.closed || []).reduce((sum, t) => {
    const ts = Date.parse(t.closedAt);
    if (!isFinite(ts) || ts < dayStart) return sum;
    return sum + (Number(t.realizedPnl) || 0);
  }, 0);
  return realizedToday + accountUnrealized(acct);
}

function renderAccountPanel() {
  if (!els.accountEquity) return;
  const acct = getPaperAccount();
  const equity = acct.cash + accountUnrealized(acct);
  const today = accountTodayPnl(acct, new Date());
  const up = today >= 0;
  const sign = up ? "+" : "-";
  els.accountEquity.textContent = formatUsd(equity);
  if (els.accountCash) els.accountCash.textContent = formatUsd(acct.cash);
  if (els.accountOpen) els.accountOpen.textContent = String((acct.positions || []).length);
  if (els.accountToday) {
    els.accountToday.textContent = `${sign}${formatUsd(Math.abs(today))}`;
    els.accountToday.className = `mono ${up ? "pnl-up" : "pnl-down"}`;
  }
}

function resetPaperAccount() {
  if (!window.confirm("Reset paper account to $10,000? This wipes cash and all positions.")) return;
  savePaperAccount(defaultPaperAccount(new Date().toISOString()));
  renderPaperBalance();
  renderPositions();
  renderRiskPage();
  renderAiRisk();
  renderJournal();
  renderOrders();
}

// ---- Live prices + positions (E3: Delta India WS ticks drive P&L) ----
// Delta Exchange India public WebSocket — no API key needed for v2/ticker
// Docs: https://docs.delta.exchange/  — Production WS: wss://socket.india.delta.exchange
// Channels: v2/ticker for perpetual futures (BTCUSD etc). Metals/commodities/forex stay on Yahoo Finance.
const DELTA_WS_URL = "wss://socket.india.delta.exchange";
const DELTA_SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD", "DOGEUSD"];
const DELTA_SYMBOL_TO_ASSET = {
  BTCUSD: "BTC",
  ETHUSD: "ETH",
  SOLUSD: "SOL",
  BNBUSD: "BNB",
  XRPUSD: "XRP",
  DOGEUSD: "DOGE",
};
// Note: Delta only lists perpetual futures for these 6 majors. Full coin-list replacement beyond these 6
// will be handled in next phase — if a coin has no Delta market we log a warning and fall back to report price.
const LIVE_TICK_STALE_MS = 60000;
let deltaWs = null;
let deltaReconnectTimer = null;
const liveTicks = {};

function scheduleDeltaReconnect() {
  if (deltaReconnectTimer) clearTimeout(deltaReconnectTimer);
  console.log("[delta] reconnecting in 3s…");
  deltaReconnectTimer = setTimeout(connectDelta, 3000);
}

function handleDeltaTick(msg) {
  if (!msg || msg.type !== "v2/ticker" || !msg.symbol) return;
  const asset = DELTA_SYMBOL_TO_ASSET[msg.symbol];
  if (!asset) {
    // Limitation: Delta has no market for this symbol — keep using report price (see note above)
    console.warn(`[delta] no mapping for ${msg.symbol}, skipping`);
    return;
  }
  const price = parseFloat(msg.mark_price ?? msg.close ?? msg.spot_price);
  if (isNaN(price)) return;
  let change = parseFloat(msg.mark_change_24h ?? msg.ltp_change_24h);
  if (isNaN(change)) change = null;
  const firstTick = !liveTicks[asset];
  liveTicks[asset] = {
    price,
    change_24h: change,
    ts: Date.now(),
    source: "Delta India",
  };
  if (firstTick) {
    console.log(`[delta] first ${asset} tick: ${formatUsd(price)} (Delta India)`);
  }
  renderPositions();
  renderRiskPage();
  renderAiRisk();
  renderPaperBalance();
}

function connectDelta() {
  if (typeof WebSocket === "undefined") {
    console.warn("[delta] WebSocket not supported in this browser");
    return;
  }
  if (deltaWs && (deltaWs.readyState === WebSocket.OPEN || deltaWs.readyState === WebSocket.CONNECTING)) {
    return;
  }
  try {
    console.log("[delta] connecting…");
    deltaWs = new WebSocket(DELTA_WS_URL);
  } catch (err) {
    console.warn("[delta] failed to open socket:", err);
    scheduleDeltaReconnect();
    return;
  }
  deltaWs.onopen = () => {
    console.log("[delta] connected, subscribing to v2/ticker…");
    deltaWs.send(JSON.stringify({
      type: "subscribe",
      payload: { channels: [{ name: "v2/ticker", symbols: DELTA_SYMBOLS }] },
    }));
  };
  deltaWs.onmessage = (event) => {
    let msg = null;
    try {
      msg = JSON.parse(event.data);
    } catch (err) {
      return;
    }
    if (msg && msg.type === "subscriptions") {
      console.log("[delta] subscription confirmed", JSON.stringify(msg.channels));
      return;
    }
    if (msg && msg.type === "error") {
      console.warn("[delta] feed error:", event.data);
      return;
    }
    handleDeltaTick(msg);
  };
  deltaWs.onerror = (err) => {
    console.warn("[delta] socket error:", err && err.message ? err.message : err);
    try { deltaWs.close(); } catch (closeErr) { /* onclose will schedule reconnect */ }
  };
  deltaWs.onclose = (event) => {
    console.warn(`[delta] closed (code ${event && event.code}), will retry…`);
    scheduleDeltaReconnect();
  };
}

// Backward-compat aliases (in case any other code still references coinbase)
const connectCoinbase = connectDelta;
const scheduleCoinbaseReconnect = scheduleDeltaReconnect;
const handleCoinbaseTick = handleDeltaTick;

function positionLivePrice(symbol, entryPrice) {
  const live = liveTicks[symbol];
  if (live && Date.now() - live.ts < LIVE_TICK_STALE_MS) return live.price;
  if (!report) return entryPrice;
  const market = [...(report.markets || []), ...(report.metals || [])]
    .find((m) => m.symbol === symbol);
  const price = market ? Number(market.price) : NaN;
  return isFinite(price) && price > 0 ? price : entryPrice;
}

function positionPnl(position, curPrice) {
  const qty = Number(position.qty) || 0;
  const entry = Number(position.entryPrice) || 0;
  const notional = Number(position.notionalUsd) || 0;
  const pnl = position.side === "SHORT"
    ? (entry - curPrice) * qty
    : (curPrice - entry) * qty;
  const pct = notional > 0 ? (pnl / notional) * 100 : 0;
  return { pnl, pct };
}

function accountUnrealized(acct) {
  return (acct.positions || []).reduce((sum, p) => {
    const cur = positionLivePrice(p.symbol, Number(p.entryPrice) || 0);
    return sum + positionPnl(p, cur).pnl;
  }, 0);
}

function renderPositions() {
  if (!els.positionsBody) return;
  const acct = getPaperAccount();
  const positions = acct.positions || [];
  if (!positions.length) {
    els.positionsBody.innerHTML = `<tr><td colspan="9" class="empty">No open positions — use Execute Trade to open one.</td></tr>`;
    return;
  }
  els.positionsBody.innerHTML = positions
    .map((p) => {
      const cur = positionLivePrice(p.symbol, Number(p.entryPrice) || 0);
      const { pnl, pct } = positionPnl(p, cur);
      const up = pnl >= 0;
      const sign = up ? "+" : "-";
      const sideClass = p.side === "SHORT" ? "pos-short" : "pos-long";
      return `
      <tr data-position-id="${p.id}">
        <td><span class="symbol-cell">${p.symbol}</span></td>
        <td><span class="pos-side ${sideClass}">${p.side}</span></td>
        <td>${formatUsd(Number(p.entryPrice) || 0)}</td>
        <td>${formatQuote(Number(p.qty) || 0)}</td>
        <td>${formatUsd(Number(p.notionalUsd) || 0)}</td>
        <td>${formatUsd(cur)}</td>
        <td class="${up ? "pnl-up" : "pnl-down"}">${sign}${formatUsd(Math.abs(pnl))}</td>
        <td class="${up ? "pnl-up" : "pnl-down"}">${sign}${Math.abs(pct).toFixed(2)}%</td>
        <td><button type="button" class="pos-close" data-close-position="${p.id}">Close</button></td>
      </tr>`;
    })
    .join("");
}

function closePosition(id) {
  const acct = getPaperAccount();
  const idx = (acct.positions || []).findIndex((p) => p.id === id);
  if (idx === -1) return;
  const pos = acct.positions[idx];
  const exitPrice = positionLivePrice(pos.symbol, Number(pos.entryPrice) || 0);
  const { pnl } = positionPnl(pos, exitPrice);
  const notional = Number(pos.notionalUsd) || 0;
  acct.cash = Math.round((acct.cash + notional + pnl) * 100) / 100;
  acct.positions.splice(idx, 1);
  acct.closed.push({
    ...pos,
    exitPrice,
    realizedPnl: Math.round(pnl * 100) / 100,
    closedAt: new Date().toISOString(),
  });
  savePaperAccount(acct);
  renderPaperBalance();
  renderPositions();
  renderJournal();
  renderOrders();
  renderRiskPage();
  renderAiRisk();
  const sign = pnl >= 0 ? "+" : "-";
  showTradeToast(`Closed ${pos.side === "SHORT" ? "short" : "long"} ${pos.symbol} @ ${formatUsd(exitPrice)} (${sign}${formatUsd(Math.abs(pnl))}) — balance ${formatUsd(acct.cash)}`);
}

function journalStats(closed) {
  const total = closed.length;
  const wins = closed.filter((t) => Number(t.realizedPnl) > 0);
  const losses = closed.filter((t) => Number(t.realizedPnl) < 0);
  const sum = (list) => list.reduce((s, t) => s + Number(t.realizedPnl), 0);
  const totalPnl = sum(closed);
  return {
    total,
    winRate: total ? (wins.length / total) * 100 : null,
    totalPnl,
    avgWin: wins.length ? sum(wins) / wins.length : null,
    avgLoss: losses.length ? sum(losses) / losses.length : null,
    best: wins.length ? Math.max(...wins.map((t) => Number(t.realizedPnl))) : null,
    worst: losses.length ? Math.min(...losses.map((t) => Number(t.realizedPnl))) : null,
  };
}

function statCard(label, value, valueClass) {
  return `<div class="stat-card"><span class="stat-label">${label}</span><span class="stat-value${valueClass ? ` ${valueClass}` : ""}">${value}</span></div>`;
}

function signedUsd(value) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  const sign = value >= 0 ? "+" : "-";
  return `${sign}${formatUsd(Math.abs(value))}`;
}

function renderJournal() {
  if (!els.journalBody && !els.journalStats) return;
  const closed = [...(getPaperAccount().closed || [])].sort(
    (a, b) => String(b.closedAt || "").localeCompare(String(a.closedAt || ""))
  );
  if (els.journalStats) {
    const stats = journalStats(closed);
    const pnlClass = (v) => (v === null ? "" : v >= 0 ? "pnl-up" : "pnl-down");
    els.journalStats.innerHTML =
      statCard("Trades", String(stats.total)) +
      statCard("Win rate", stats.winRate === null ? "—" : `${stats.winRate.toFixed(1)}%`) +
      statCard("Total P&L", signedUsd(stats.totalPnl), pnlClass(stats.totalPnl)) +
      statCard("Avg win", stats.avgWin === null ? "—" : signedUsd(stats.avgWin), "pnl-up") +
      statCard("Avg loss", stats.avgLoss === null ? "—" : signedUsd(stats.avgLoss), "pnl-down") +
      statCard("Best", stats.best === null ? "—" : signedUsd(stats.best), "pnl-up") +
      statCard("Worst", stats.worst === null ? "—" : signedUsd(stats.worst), "pnl-down");
  }
  if (!els.journalBody) return;
  if (!closed.length) {
    els.journalBody.innerHTML = `<tr><td colspan="8" class="empty">No closed trades yet — closed positions will appear here.</td></tr>`;
    return;
  }
  els.journalBody.innerHTML = closed
    .map((t) => {
      const pnl = Number(t.realizedPnl) || 0;
      const notional = Number(t.notionalUsd) || 0;
      const pct = notional > 0 ? (pnl / notional) * 100 : null;
      const up = pnl >= 0;
      const sign = up ? "+" : "-";
      const sideClass = t.side === "SHORT" ? "pos-short" : "pos-long";
      return `
      <tr>
        <td><span class="symbol-cell">${t.symbol}</span></td>
        <td><span class="pos-side ${sideClass}">${t.side}</span></td>
        <td>${formatUsd(Number(t.entryPrice) || 0)}</td>
        <td>${t.exitPrice !== null && t.exitPrice !== undefined ? formatUsd(Number(t.exitPrice)) : "—"}</td>
        <td>${formatUsd(notional)}</td>
        <td class="${up ? "pnl-up" : "pnl-down"}">${sign}${formatUsd(Math.abs(pnl))}</td>
        <td class="${up ? "pnl-up" : "pnl-down"}">${pct === null ? "—" : `${sign}${Math.abs(pct).toFixed(2)}%`}</td>
        <td>${t.closedAt ? formatTime(t.closedAt) : "—"}</td>
      </tr>`;
    })
    .join("");
}

function renderOrders() {
  if (!els.ordersBody) return;
  const acct = getPaperAccount();
  const orders = [
    ...(acct.positions || []).map((p) => ({
      symbol: p.symbol,
      side: p.side,
      entryPrice: p.entryPrice,
      notionalUsd: p.notionalUsd,
      status: "Open",
      time: p.openedAt,
    })),
    ...(acct.closed || []).map((t) => ({
      symbol: t.symbol,
      side: t.side,
      entryPrice: t.entryPrice,
      notionalUsd: t.notionalUsd,
      status: "Closed",
      time: t.closedAt,
    })),
  ].sort((a, b) => String(b.time || "").localeCompare(String(a.time || "")));
  if (!orders.length) {
    els.ordersBody.innerHTML = `<tr><td colspan="6" class="empty">No orders yet — use Execute Trade to place one.</td></tr>`;
    return;
  }
  els.ordersBody.innerHTML = orders
    .map((o) => `
      <tr>
        <td><span class="symbol-cell">${o.symbol}</span></td>
        <td><span class="pos-side ${o.side === "SHORT" ? "pos-short" : "pos-long"}">${o.side}</span></td>
        <td>${formatUsd(Number(o.entryPrice) || 0)}</td>
        <td>${formatUsd(Number(o.notionalUsd) || 0)}</td>
        <td><span class="order-status ${o.status === "Open" ? "order-open" : "order-closed"}">${o.status}</span></td>
        <td>${o.time ? formatTime(o.time) : "—"}</td>
      </tr>`)
    .join("");
}

// ---- Place Trade (E2: simulated market orders at live report price) ----
let tradeSide = "LONG";
let tradeToastTimer = null;

function tradeAssets() {
  if (!report) return [];
  return [...(report.markets || []), ...(report.metals || [])];
}

function tradePriceFor(symbol) {
  const asset = tradeAssets().find((m) => m.symbol === symbol);
  const price = asset ? Number(asset.price) : NaN;
  return isFinite(price) && price > 0 ? price : null;
}

function chartSymbolToAsset(tvSymbol) {
  if (!tvSymbol || !report) return null;
  const hit = tradeAssets().find((m) => getChartSymbol(m) === tvSymbol);
  return hit ? hit.symbol : null;
}

function isTradeOpen() {
  return !!(els.tradeModal && !els.tradeModal.hidden);
}

function closeTradeModal() {
  if (els.tradeModal) els.tradeModal.hidden = true;
}

function setTradeError(msg) {
  if (!els.tradeError) return;
  if (!msg) {
    els.tradeError.hidden = true;
    els.tradeError.textContent = "";
  } else {
    els.tradeError.hidden = false;
    els.tradeError.textContent = msg;
  }
}

function setTradeSide(side) {
  tradeSide = side === "SHORT" ? "SHORT" : "LONG";
  if (els.tradeLong) els.tradeLong.classList.toggle("is-active", tradeSide === "LONG");
  if (els.tradeShort) els.tradeShort.classList.toggle("is-active", tradeSide === "SHORT");
}

function refreshTradePrice() {
  if (!els.tradeSymbol) return;
  const price = tradePriceFor(els.tradeSymbol.value);
  if (els.tradePrice) {
    els.tradePrice.textContent = price === null ? "—" : formatUsd(price);
  }
  const amount = els.tradeAmount ? parseFloat(els.tradeAmount.value) : NaN;
  if (els.tradeQty) {
    if (price !== null && isFinite(amount) && amount > 0) {
      els.tradeQty.textContent = `≈ ${formatQuote(amount / price)} ${els.tradeSymbol.value}`;
    } else {
      els.tradeQty.textContent = "";
    }
  }
  if (els.tradePlace) els.tradePlace.disabled = price === null;
}

function openTradeModal() {
  if (!els.tradeModal || !els.tradeSymbol) return;
  const assets = tradeAssets();
  els.tradeSymbol.innerHTML = assets.length
    ? assets.map((m) => `<option value="${m.symbol}">${m.symbol} — ${m.name || ""}</option>`).join("")
    : `<option value="">No market data</option>`;
  const chartAsset = chartSymbolToAsset(currentChartSymbol);
  els.tradeSymbol.value = chartAsset && assets.some((m) => m.symbol === chartAsset) ? chartAsset : "BTC";
  if (!assets.some((m) => m.symbol === els.tradeSymbol.value) && assets.length) {
    els.tradeSymbol.value = assets[0].symbol;
  }
  setTradeSide("LONG");
  if (els.tradeAmount) els.tradeAmount.value = "";
  setTradeError(null);
  refreshTradePrice();
  els.tradeModal.hidden = false;
}

function showTradeToast(msg) {
  if (!els.tradeToast) return;
  els.tradeToast.textContent = msg;
  els.tradeToast.hidden = false;
  if (tradeToastTimer) clearTimeout(tradeToastTimer);
  tradeToastTimer = setTimeout(() => {
    if (els.tradeToast) els.tradeToast.hidden = true;
  }, 4500);
}

function submitTrade() {
  setTradeError(null);
  const symbol = els.tradeSymbol ? els.tradeSymbol.value : "";
  const price = tradePriceFor(symbol);
  if (price === null) {
    setTradeError("Live price unavailable — refresh data and try again.");
    if (els.tradePlace) els.tradePlace.disabled = true;
    return;
  }
  const amount = els.tradeAmount ? parseFloat(els.tradeAmount.value) : NaN;
  if (!isFinite(amount) || amount <= 0) {
    setTradeError("Enter an amount greater than 0.");
    return;
  }
  const acct = getPaperAccount();
  if (amount > acct.cash) {
    setTradeError(`Insufficient funds — available ${formatUsd(acct.cash)}.`);
    return;
  }
  const now = new Date().toISOString();
  acct.cash = Math.round((acct.cash - amount) * 100) / 100;
  acct.positions.push({
    id: "t" + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36),
    symbol,
    side: tradeSide,
    qty: amount / price,
    notionalUsd: amount,
    entryPrice: price,
    openedAt: now,
  });
  savePaperAccount(acct);
  renderPaperBalance();
  renderOrders();
  renderRiskPage();
  renderAiRisk();
  closeTradeModal();
  showTradeToast(`Filled ${tradeSide === "LONG" ? "long" : "short"} ${formatUsd(amount)} ${symbol} @ ${formatUsd(price)} — balance ${formatUsd(acct.cash)}`);
}

let clockTimer = null;
function startClock() {
  if (clockTimer) clearInterval(clockTimer);
  tickClock();
  clockTimer = setInterval(tickClock, 1000);
}

function applyTheme(theme) {
  activeTheme = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", activeTheme);
  try {
    localStorage.setItem("pulse-theme", activeTheme);
  } catch (err) {
    // localStorage unavailable — theme still applies for this session
  }
  if (els.themeToggle) {
    els.themeToggle.setAttribute(
      "aria-label",
      activeTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"
    );
  }
  if (els.settingsThemeLabel) els.settingsThemeLabel.textContent = activeTheme === "light" ? "Light" : "Dark";
}

function syncSettingsDisplay() {
  if (els.settingsTimezone) els.settingsTimezone.value = activeTimezone;
  if (els.settingsThemeLabel) els.settingsThemeLabel.textContent = activeTheme === "light" ? "Light" : "Dark";
}

function renderSettings() {
  const acct = getPaperAccount();
  const equity = acct.cash + accountUnrealized(acct);
  if (els.settingsBalance) els.settingsBalance.textContent = formatUsd(acct.cash);
  if (els.settingsPositions) els.settingsPositions.textContent = String((acct.positions || []).length);
  if (els.settingsEquity) els.settingsEquity.textContent = formatUsd(equity);
  if (els.settingsWatchlist) {
    els.settingsWatchlist.innerHTML = WATCHLIST.map(
      (c) => `<li><span class="wl-sym">${c.symbol}</span><span class="wl-name">${c.name}</span></li>`
    ).join("");
  }
  syncSettingsDisplay();
}

function setTimezone(tz) {
  if (!TIMEZONES[tz]) return;
  activeTimezone = tz;
  try {
    localStorage.setItem("pulse-timezone", tz);
  } catch (err) {
    // localStorage unavailable — selection still applies for this session
  }
  if (els.timezoneSelect) els.timezoneSelect.value = tz;
  syncSettingsDisplay();
  refreshTimestamps();
  tickClock();
}

function relativeTime(iso) {
  const delta = Date.now() - new Date(iso).getTime();
  const minutes = Math.max(0, Math.round(delta / 60000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function changeClass(value) {
  if (value > 0) return "is-up";
  if (value < 0) return "is-down";
  return "";
}

function formatChange(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function formatQuote(value) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  const digits = value >= 100 ? 2 : value >= 1 ? 4 : 5;
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function matchesQuery(text, query) {
  return text.toLowerCase().includes(query);
}

function renderScanner(trendingCoins) {
  if (!els.scannerBody) return;
  if (!trendingCoins || trendingCoins.length === 0) {
    els.scannerBody.innerHTML = `<tr><td colspan="6" class="empty">No trending data available</td></tr>`;
    return;
  }

  els.scannerBody.innerHTML = trendingCoins
    .map(
      (coin) => `
      <tr>
        <td><span class="scanner-symbol">${coin.symbol}</span></td>
        <td><span class="scanner-name">${coin.name}</span></td>
        <td><span class="scanner-price">${formatUsd(coin.price)}</span></td>
        <td><span class="scanner-change ${changeClass(coin.change_24h)}">${formatChange(coin.change_24h)}</span></td>
        <td><span class="scanner-volume">${formatCompact(coin.volume)}</span></td>
        <td><span class="scanner-score">${coin.trending_score}</span></td>
      </tr>`
    )
    .join("");
}

function initTradingView(symbol = "BTCUSD") {
  if (els.chartContainer && typeof TradingView !== "undefined") {
    els.chartContainer.innerHTML = "";
    new TradingView.widget({
      width: "100%",
      height: 400,
      symbol: symbol,
      interval: String(currentTimeframe),
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      toolbar_bg: "#1c1a15",
      enable_publishing: false,
      allow_symbol_change: true,
      container_id: "tradingview-widget",
      hide_side_toolbar: false,
      overrides: {
        "mainSeriesProperties.showCountdown": true
      }
    });
  }
}

// ---- Candle countdown (Approach 2 overlay fallback) ----
function getCandleRemainingSec() {
  const now = new Date();
  const tf = currentTimeframe;
  const intervalMs = tf * 60 * 1000;
  // Use UTC to align with TradingView's Etc/UTC interval
  const msIntoInterval = (now.getUTCMinutes() % tf) * 60000 + now.getUTCSeconds() * 1000 + now.getUTCMilliseconds();
  const msRemaining = intervalMs - msIntoInterval;
  let totalSec = Math.ceil(msRemaining / 1000);
  if (totalSec <= 0) totalSec = tf * 60;
  if (totalSec > tf * 60) totalSec = tf * 60;
  return totalSec;
}

function formatCountdown(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function updateCountdown() {
  const el = els.candleCountdown || document.getElementById("candle-countdown");
  if (!el) return;
  const sec = getCandleRemainingSec();
  el.textContent = `Closes in: ${formatCountdown(sec)}`;
}

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer);
  updateCountdown();
  countdownTimer = setInterval(updateCountdown, 1000);
}

function setTimeframe(tf) {
  const parsed = parseInt(tf, 10);
  if (![1, 30, 60].includes(parsed)) return;
  currentTimeframe = parsed;
  document.querySelectorAll(".chart-tf-btn").forEach((btn) => {
    btn.classList.toggle("is-active", parseInt(btn.dataset.tf, 10) === parsed);
  });
  initTradingView(currentChartSymbol);
  startCountdown();
}

function setLoading(loading) {
  isLoading = loading;
  if (els.refreshBtn) {
    els.refreshBtn.disabled = loading;
    els.refreshBtn.classList.toggle("is-loading", loading);
  }
}

function renderNews() {
  const query = els.search.value.trim().toLowerCase();
  const rows = report.news.filter((item) => {
    const inFilter = activeFilter === "All" || item.category === activeFilter;
    const haystack = `${item.title} ${item.source} ${item.category}`;
    return inFilter && matchesQuery(haystack, query);
  });

  if (!rows.length) {
    els.news.innerHTML = `<p class="empty">No wire items match this view.</p>`;
    return;
  }

  els.news.innerHTML = rows
    .map(
      (item) => `
      <a class="news-item" href="${item.url}" target="_blank" rel="noopener noreferrer">
        <span class="news-time">${formatTime(item.published_at)}</span>
        <div>
          <p class="news-title">${item.title}</p>
          <p class="news-source">${item.source}</p>
        </div>
        <span class="news-cat">${item.category}</span>
      </a>`
    )
    .join("");
}

function renderListings() {
  const query = els.search.value.trim().toLowerCase();
  const rows = report.listings.filter((item) =>
    matchesQuery(`${item.name} ${item.symbol} ${item.note}`, query)
  );

  if (!rows.length) {
    els.listings.innerHTML = `<tr><td colspan="3" class="empty">No listings match this search.</td></tr>`;
    return;
  }

  els.listings.innerHTML = rows
    .map(
      (item) => `
      <tr>
        <td><a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.name}</a></td>
        <td class="symbol-cell">${item.symbol}</td>
        <td>${item.note}</td>
      </tr>`
    )
    .join("");
}

function getChartSymbol(market) {
  try {
    const url = new URL(market.chart_url);
    const symbol = url.searchParams.get("symbol");
    if (symbol) return symbol;
  } catch (error) {
    // Fall back to the market symbol below.
  }
  return `${market.symbol}USD`;
}

function switchChart(symbol) {
  if (!symbol || symbol === currentChartSymbol) return;
  currentChartSymbol = symbol;
  document.querySelectorAll(".chart-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.symbol === symbol);
  });
  initTradingView(symbol);
}

function renderChartControls(markets, metals = []) {
  if (!els.chartControls) return;

  const allMarkets = [...markets, ...metals];
  const deltaMajors = new Set(["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]);

  els.chartControls.innerHTML = allMarkets
    .map((market) => {
      const symbol = getChartSymbol(market);
      const isCrypto = deltaMajors.has(market.symbol);
      const deltaUrl = isCrypto ? getDeltaTradeUrl(market.symbol) : null;
      const deltaLink = deltaUrl
        ? `<a href="${deltaUrl}" target="_blank" rel="noopener" class="chart-delta-link" title="Trade ${market.symbol} on Delta India" aria-label="Trade ${market.symbol} on Delta India" onclick="event.stopPropagation()">Trade ↗</a>`
        : "";
      if (deltaUrl) {
        return `<div class="chart-btn-group">
        <button
          type="button"
          class="chart-btn ${symbol === currentChartSymbol ? "is-active" : ""}"
          data-symbol="${symbol}"
        >${market.symbol}</button>${deltaLink}</div>`;
      }
      return `
        <button
          type="button"
          class="chart-btn ${symbol === currentChartSymbol ? "is-active" : ""}"
          data-symbol="${symbol}"
        >${market.symbol}</button>`;
    })
    .join("");
}

function startReportPolling() {
  if (reportTimer) clearInterval(reportTimer);
  reportTimer = setInterval(() => {
    try {
      loadReport();
    } catch (err) {
      console.warn("Scheduled full refresh failed:", err);
    }
  }, 120000);
}

function getFailedSources(errors, report) {
  if (!errors || typeof errors !== "object") return [];

  const failedSources = [];
  const sourceToDataKey = {
    markets: "markets",
    news: "news",
    listings: "listings",
    trending: "trending",
    metals: "metals",
    commodities_forex: "commodities_forex",
  };

  for (const [source, sourceErrors] of Object.entries(errors)) {
    const dataKey = sourceToDataKey[source];
    const hasErrors = Array.isArray(sourceErrors) && sourceErrors.some((item) => String(item).trim());
    const dataIsEmpty = dataKey && report && (!report[dataKey] || report[dataKey].length === 0);
    
    if (hasErrors && dataIsEmpty) {
      failedSources.push(source.charAt(0).toUpperCase() + source.slice(1));
    }
  }

  return failedSources;
}

function renderErrorBanner(errors) {
  if (!els.errorBanner) return;

  const failedSources = getFailedSources(errors, report);
  if (!failedSources.length) {
    els.errorBanner.hidden = true;
    els.errorBanner.textContent = "";
    return;
  }

  els.errorBanner.hidden = false;
  els.errorBanner.textContent = `Some data sources failed: ${failedSources.join(", ")}`;
}

function renderAiBriefing(aiBriefing) {
  if (!aiBriefing) {
    if (els.aiMorningSummary) els.aiMorningSummary.textContent = "AI briefing not available";
    if (els.aiWatchList) els.aiWatchList.innerHTML = "<li>No AI watch items available</li>";
    if (els.marketSentiment) {
      els.marketSentiment.textContent = "Unknown";
      els.marketSentiment.className = "sentiment-badge sentiment-unknown";
    }
    if (els.aiFullMorningSummary) els.aiFullMorningSummary.textContent = "AI briefing not available";
    if (els.aiFullWatchList) els.aiFullWatchList.innerHTML = "<li>No AI watch items available</li>";
    if (els.aiFullMarketSentiment) {
      els.aiFullMarketSentiment.textContent = "Unknown";
      els.aiFullMarketSentiment.className = "sentiment-badge sentiment-unknown";
    }
    return;
  }

  const summary = aiBriefing.morning_summary || "AI briefing unavailable";
  const sentiment = aiBriefing.market_sentiment || "unknown";
  const sentimentLabel = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
  const sentimentClass = `sentiment-badge sentiment-${sentiment}`;
  const watchItems = aiBriefing.things_to_watch || [];
  const watchHtml = watchItems.length === 0
    ? "<li>No watch items available</li>"
    : watchItems.map((item) => `<li>${item}</li>`).join("");

  if (els.aiMorningSummary) els.aiMorningSummary.textContent = summary;
  if (els.marketSentiment) {
    els.marketSentiment.textContent = sentimentLabel;
    els.marketSentiment.className = sentimentClass;
  }
  if (els.aiWatchList) els.aiWatchList.innerHTML = watchHtml;

  if (els.aiFullMorningSummary) els.aiFullMorningSummary.textContent = summary;
  if (els.aiFullMarketSentiment) {
    els.aiFullMarketSentiment.textContent = sentimentLabel;
    els.aiFullMarketSentiment.className = sentimentClass;
  }
  if (els.aiFullWatchList) els.aiFullWatchList.innerHTML = watchHtml;
}

function renderTopSetup(topSetup, targetEl = els.topSetupContent) {
  if (!targetEl) return;
  
  if (!topSetup || topSetup.note) {
    targetEl.innerHTML = `
      <div class="top-setup-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 8v4M12 16h.01"/>
        </svg>
        <p>No high-quality setup right now</p>
        <span>The scanner found signals but none met the confidence threshold (score ≥ 60).</span>
      </div>`;
    return;
  }

  const dirClass = topSetup.direction === "LONG" ? "dir-long" : "dir-short";
  const entryStr = Array.isArray(topSetup.entry_zone) 
    ? `${formatUsd(topSetup.entry_zone[0])} – ${formatUsd(topSetup.entry_zone[1])}`
    : formatUsd(topSetup.entry_zone);
  const targetsStr = Array.isArray(topSetup.targets)
    ? topSetup.targets.map(t => formatUsd(t)).join(" / ")
    : (topSetup.targets ? formatUsd(topSetup.targets) : "—");

  const deltaUrl = getDeltaTradeUrl(topSetup.symbol);
  const symbolHtml = deltaUrl
    ? `<a href="${deltaUrl}" target="_blank" rel="noopener" class="top-setup-symbol top-setup-delta-link" title="Trade ${topSetup.symbol} on Delta India" aria-label="Trade ${topSetup.symbol} on Delta India">${topSetup.symbol} ↗</a>`
    : `<span class="top-setup-symbol">${topSetup.symbol}</span>`;

  targetEl.innerHTML = `
      <div class="top-setup-header">
        <div>
          ${symbolHtml}
          <span class="top-setup-direction ${dirClass}">${topSetup.direction}</span>
        </div>
        <span class="top-setup-score">Score: ${topSetup.score}</span>
      </div>
      <div class="top-setup-grid">
        <div class="top-setup-field">
          <span class="top-setup-label">Entry Zone</span>
          <span class="top-setup-value">${entryStr}</span>
        </div>
        <div class="top-setup-field">
          <span class="top-setup-label">Stop Loss</span>
          <span class="top-setup-value">${topSetup.stop_loss ? formatUsd(topSetup.stop_loss) : "—"}</span>
        </div>
        <div class="top-setup-field">
          <span class="top-setup-label">Targets (TP1/TP2/TP3)</span>
          <span class="top-setup-value">${targetsStr}</span>
        </div>
        <div class="top-setup-field">
          <span class="top-setup-label">Risk/Reward</span>
          <span class="top-setup-value">${topSetup.risk_reward || "—"}</span>
        </div>
      </div>
      <div class="top-setup-reasons">
        <span class="top-setup-label">Reasons</span>
        <div class="top-setup-tags">
          ${topSetup.reasons.map(r => `<span class="top-setup-tag">${r}</span>`).join("")}
        </div>
      </div>
      <div class="top-setup-invalidation">
        <span class="top-setup-label">Invalidation</span>
        <span class="top-setup-value">${topSetup.invalidation || "—"}</span>
      </div>
    </div>`;
}

function renderSetupsTable(setups, tbodyEl = els.setupBody) {
  if (!tbodyEl) return;
  
  if (!setups || setups.length === 0) {
    tbodyEl.innerHTML = `<tr><td colspan="8" class="empty">No setup data available</td></tr>`;
    return;
  }

  tbodyEl.innerHTML = setups
    .map((s) => {
      const dirClass = s.direction === "LONG" ? "dir-long" : 
                       s.direction === "SHORT" ? "dir-short" : "dir-none";
      const entryStr = Array.isArray(s.entry_zone) 
        ? `${formatUsd(s.entry_zone[0])} – ${formatUsd(s.entry_zone[1])}`
        : (s.entry_zone ? formatUsd(s.entry_zone) : "—");
      const targetsStr = Array.isArray(s.targets)
        ? s.targets.map(t => formatUsd(t)).join(" / ")
        : (s.targets ? formatUsd(s.targets) : "—");

      return `
      <tr>
        <td><span class="setup-symbol">${s.symbol}</span></td>
        <td><span class="setup-direction ${dirClass}">${s.direction}</span></td>
        <td><span class="setup-score">${s.score}</span></td>
        <td class="setup-reasons">${s.reasons.map(r => `<span class="setup-tag">${r}</span>`).join(" ")}</td>
        <td>${entryStr}</td>
        <td>${s.stop_loss ? formatUsd(s.stop_loss) : "—"}</td>
        <td>${targetsStr}</td>
        <td>${s.risk_reward || "—"}</td>
      </tr>`;
    })
    .join("");
}

function renderNewTrending(list) {
  const tbody = els.newTrendingBody;
  if (!tbody) return;
  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty">No new or trending coins right now — check back after the next Delta scan.</td></tr>`;
    return;
  }
  tbody.innerHTML = list.map((c) => {
    const dirClass = c.momentum_direction === "LONG" ? "dir-long" : c.momentum_direction === "SHORT" ? "dir-short" : "dir-none";
    const badgeClass = c.badge === "Early Signal" ? "badge-early" : "badge-momentum";
    const deltaUrl = getDeltaTradeUrl(c.symbol, c.contract);
    const deltaLink = deltaUrl ? `<a href="${deltaUrl}" target="_blank" rel="noopener" class="md-delta-link" title="Trade ${c.symbol} on Delta India" aria-label="Trade ${c.symbol} on Delta India" onclick="event.stopPropagation()">Trade ↗</a>` : "";
    const whyClass = c.why.includes("New listing") ? "flag-new" : c.why.includes("High volume") ? "flag-volume" : "flag-trending";
    return `
      <tr>
        <td><span class="setup-symbol">${c.symbol}</span> ${deltaLink}</td>
        <td><span class="${whyClass}">${c.why}</span></td>
        <td><span class="setup-direction ${dirClass}">${c.momentum_direction}</span></td>
        <td><span class="${badgeClass}">${c.badge}</span><br><span class="top-setup-label">${c.strength}</span></td>
        <td>${c.price != null ? formatUsd(c.price) : "—"}</td>
        <td class="${changeClass(c.change_24h)}">${c.change_24h != null ? formatChange(c.change_24h) : "—"}</td>
        <td>${c.momentum_pct != null ? `${c.momentum_pct > 0 ? "+" : ""}${c.momentum_pct.toFixed(2)}%` : "—"}</td>
        <td>${c.volume_spike != null ? `${c.volume_spike.toFixed(2)}x` : "—"}</td>
      </tr>`;
  }).join("");
}

function computeRiskSummary(acct) {
  const positions = (acct && acct.positions) || [];
  const equity = (acct ? Number(acct.cash) : 0) + (acct ? accountUnrealized(acct) : 0);
  const byAsset = {};
  positions.forEach((p) => {
    const size = Number(p.notionalUsd) || 0;
    if (!byAsset[p.symbol]) byAsset[p.symbol] = { symbol: p.symbol, exposure: 0, count: 0 };
    byAsset[p.symbol].exposure += size;
    byAsset[p.symbol].count += 1;
  });
  const assets = Object.values(byAsset)
    .map((a) => ({
      ...a,
      pctEquity: equity > 0 ? (a.exposure / equity) * 100 : 0,
    }))
    .sort((a, b) => b.exposure - a.exposure);
  const totalExposure = assets.reduce((sum, a) => sum + a.exposure, 0);
  return { positions, equity, assets, totalExposure };
}

function renderRiskPage() {
  if (!els.riskBody && !els.riskSummary) return;
  const summary = computeRiskSummary(getPaperAccount());
  if (els.riskSummary) {
    els.riskSummary.innerHTML =
      statCard("Total exposure", formatUsd(summary.totalExposure)) +
      statCard("Positions", String(summary.positions.length)) +
      statCard("Equity", formatUsd(summary.equity));
  }
  if (!els.riskBody) return;
  if (!summary.positions.length) {
    els.riskBody.innerHTML = `<tr><td colspan="4" class="empty">No open positions — nothing at risk right now.</td></tr>`;
    return;
  }
  els.riskBody.innerHTML = summary.positions
    .map((p) => {
      const size = Number(p.notionalUsd) || 0;
      const pct = summary.equity > 0 ? (size / summary.equity) * 100 : 0;
      const sideClass = p.side === "SHORT" ? "pos-short" : "pos-long";
      return `
      <tr>
        <td><span class="symbol-cell">${p.symbol}</span></td>
        <td><span class="pos-side ${sideClass}">${p.side}</span></td>
        <td>${formatUsd(size)}</td>
        <td>${pct.toFixed(1)}%</td>
      </tr>`;
    })
    .join("");
}

function renderAiSetupTab() {
  if (!report) return;
  if (els.aiSetupContent) renderTopSetup(report.top_setup, els.aiSetupContent);
  if (els.aiFullSetupContent) renderTopSetup(report.top_setup, els.aiFullSetupContent);
}

function renderAiRisk() {
  const summary = computeRiskSummary(getPaperAccount());
  const riskHtml = !summary.positions.length
    ? `<p class="empty">No open positions — nothing at risk right now.</p>`
    : `
    <div class="ai-risk-summary">
      <div><span>Exposure</span><strong>${formatUsd(summary.totalExposure)}</strong></div>
      <div><span>Equity</span><strong>${formatUsd(summary.equity)}</strong></div>
    </div>
    <ul class="ai-watch-list">
      ${summary.assets.slice(0, 3).map((a) => `<li>${a.symbol} — ${formatUsd(a.exposure)} (${a.pctEquity.toFixed(1)}% of equity)</li>`).join("")}
    </ul>`;
  if (els.aiRiskContent) els.aiRiskContent.innerHTML = riskHtml;
  if (els.aiFullRiskContent) els.aiFullRiskContent.innerHTML = riskHtml;
}

function renderReport() {
  els.updatedAt.textContent = formatTime(report.generated_at);
  els.updatedRelative.textContent = relativeTime(report.generated_at);
  renderErrorBanner(report.errors);
  renderChartControls(report.markets, report.metals);
  renderTopSetup(report.top_setup);
  renderSetupsTable(report.setups);
  renderNewTrending(report.new_trending);
  renderRiskPage();
  renderAiSetupTab();
  renderAiRisk();
  renderScanner(report.trending);
  renderNews();
  renderListings();
  renderAiBriefing(report.ai_briefing);
  renderSnapshot();
  renderPositions();
  renderJournal();
  renderOrders();
  if (mdOpen) renderMdList();
  
  initTradingView(currentChartSymbol);
}

function showError(message) {
  els.status.hidden = false;
  els.status.textContent = message;
}

function showComingSoon(viewName) {
  if (!els.comingSoonModal || !els.comingSoonMessage || !els.comingSoonTitle) return;
  
  const titles = {
    "ai-analysis": "AI Analysis",
    "execute-trade": "Execute Trade",
    "positions": "Positions",
    "orders": "Orders",
    "journal": "Trading Journal",
    "settings": "Settings"
  };

  const messages = {
    "ai-analysis": "Advanced AI analysis tabs (Top Setup, Risks) need the market scanner engine. The Market tab shows real AI briefing data.",
    "execute-trade": "Trade execution requires exchange API integration which is not built yet.",
    "positions": "Positions tracking requires exchange connection which is not built yet.",
    "orders": "Order management requires exchange connection which is not built yet.",
    "journal": "Trading journal is not built yet.",
    "settings": "Settings panel is not built yet."
  };

  els.comingSoonTitle.textContent = titles[viewName] || "Coming Soon";
  els.comingSoonMessage.textContent = messages[viewName] || "This feature is not built yet.";
  els.comingSoonModal.hidden = false;
}

function hideComingSoon() {
  if (els.comingSoonModal) {
    els.comingSoonModal.hidden = true;
  }
}

function switchView(viewName) {
  activeView = viewName;
  
  els.navItems.forEach((item) => {
    item.classList.toggle("is-active", item.dataset.view === viewName);
  });

  const comingSoonViews = [];
  
  if (comingSoonViews.includes(viewName) && viewName !== "dashboard" && viewName !== "news") {
    showComingSoon(viewName);
    return;
  }

  if (viewName === "risk") {
    const panel = document.querySelector('[aria-labelledby="risk-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "positions") {
    const panel = document.querySelector('[aria-labelledby="positions-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "orders") {
    const panel = document.querySelector('[aria-labelledby="orders-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "journal") {
    const panel = document.querySelector('[aria-labelledby="journal-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "scanner") {
    const panel = document.querySelector('[aria-labelledby="scanner-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "news") {
    const panel = document.querySelector('[aria-labelledby="news-heading"]');
    if (panel) panel.scrollIntoView({ behavior: "smooth" });
  } else if (viewName === "settings") {
    const panel = document.querySelector('[aria-labelledby="settings-heading"]');
    if (panel) {
      renderSettings();
      panel.scrollIntoView({ behavior: "smooth" });
    }
  } else if (viewName === "ai-analysis") {
    const panel = document.querySelector('[aria-labelledby="ai-analysis-heading"]');
    if (panel) {
      if (report) {
        renderAiBriefing(report.ai_briefing);
        renderAiSetupTab();
        renderAiRisk();
      } else {
        renderSettings();
      }
      panel.scrollIntoView({ behavior: "smooth" });
    }
  } else if (viewName === "dashboard") {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function switchAiTab(tabName) {
  els.aiTabs.forEach((tab) => {
    const isActive = tab.dataset.tab === tabName;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", isActive);
  });

  els.aiTabPanels.forEach((panel) => {
    const isActive = panel.id === `ai-${tabName}`;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  });

  if (tabName === "news") {
    const newsSection = document.querySelector('[aria-labelledby="news-heading"]');
    if (newsSection) {
      newsSection.scrollIntoView({ behavior: "smooth" });
    }
  }
}

function switchAiFullTab(tabName) {
  const tabs = els.aiFullTabs || document.querySelectorAll(".ai-full-panel .ai-tab");
  const panels = els.aiFullPanels || document.querySelectorAll(".ai-full-panel .ai-tab-panel");
  tabs.forEach((tab) => {
    const isActive = tab.dataset.fulltab === tabName;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", isActive);
  });
  panels.forEach((panel) => {
    const isActive = panel.id === `ai-full-${tabName}`;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  });
  if (tabName === "news") {
    const newsSection = document.querySelector('[aria-labelledby="news-heading"]');
    if (newsSection) newsSection.scrollIntoView({ behavior: "smooth" });
  }
}

function mdPrice(p) {
  if (p === null || p === undefined || isNaN(p)) return "—";
  return p >= 1 ? formatUsd(p) : `$${formatQuote(p)}`;
}

function getDeltaTradeUrl(symbol, deltaSymbol) {
  if (!symbol) return null;
  // Only for crypto — Delta doesn't offer metals/commodities/forex
  const s = String(symbol).toUpperCase().trim();
  if (!s) return null;
  // Use explicit deltaSymbol if provided (e.g., BTCUSD from API), otherwise construct as SYMBOLUSD
  let product = deltaSymbol ? String(deltaSymbol).toUpperCase().trim() : `${s}USD`;
  // Ensure it looks like a Delta perpetual (ends with USD); if already contains USD, keep as is
  if (!product.endsWith("USD") && !product.endsWith("INR")) product = `${s}USD`;
  // Verified 2026-09-15 in real browser: https://india.delta.exchange/app/trade/BTCUSD -> generic markets,
  // correct per-symbol trading/chart page is https://india.delta.exchange/app/futures/trade/BTCUSD
  // (or https://www.delta.exchange/app/futures/trade/BTC/BTCUSD) which shows live chart + orderbook
  return `https://india.delta.exchange/app/futures/trade/${product}`;
}

function mdCategoryAssets(cat) {
  if (!report) return [];
  if (cat === "crypto") {
    return (report.crypto_full || []).map((c) => ({
      symbol: c.symbol,
      name: c.name,
      price: c.price,
      change: c.change_24h_pct ?? null,
      volume: c.volume ?? null,
      mcap: c.market_cap ?? null,
      deltaSymbol: c.delta_symbol || null,
    }));
  }
  if (cat === "metals") {
    const bullion = (report.metals || []).map((m) => ({
      symbol: m.symbol,
      name: m.name,
      price: m.price,
      change: m.change_24h ?? null,
    }));
    const platinum = (report.commodities_forex || [])
      .filter((m) => METAL_SYMBOLS.includes(m.symbol))
      .map((m) => ({
        symbol: m.symbol,
        name: m.name,
        price: m.price,
        change: m.change_pct ?? null,
      }));
    return [...bullion, ...platinum];
  }
  const cf = report.commodities_forex || [];
  if (cat === "commodities") {
    return cf
      .filter((m) => m.group === "commodities" && !METAL_SYMBOLS.includes(m.symbol))
      .map((m) => ({ symbol: m.symbol, name: m.name, price: m.price, change: m.change_pct ?? null }));
  }
  return cf
    .filter((m) => m.group === "forex")
    .map((m) => ({ symbol: m.symbol, name: m.name, price: m.price, change: m.change_pct ?? null }));
}

function mdCryptoRows(query = mdQuery, filter = mdCryptoFilter) {
  let rows = mdCategoryAssets("crypto");
  const total = rows.length;
  const q = String(query || "").trim().toLowerCase();
  if (q) {
    rows = rows.filter(
      (r) =>
        String(r.symbol || "").toLowerCase().includes(q) ||
        String(r.name || "").toLowerCase().includes(q)
    );
  }
  let label;
  if (filter === "gainers") {
    rows = rows.filter((r) => r.change !== null).sort((a, b) => b.change - a.change).slice(0, MD_TOP_N);
    label = `Top ${MD_TOP_N} gainers`;
  } else if (filter === "losers") {
    rows = rows.filter((r) => r.change !== null).sort((a, b) => a.change - b.change).slice(0, MD_TOP_N);
    label = `Top ${MD_TOP_N} losers`;
  } else if (filter === "largecap") {
    rows = rows.filter((r) => (r.mcap ?? 0) >= LARGE_CAP_MIN).sort((a, b) => (b.mcap ?? 0) - (a.mcap ?? 0));
    label = `Large-cap (≥$10B)`;
  } else {
    label = `${total} assets`;
  }
  if (q) label += ` · ${rows.length} match${rows.length === 1 ? "" : "es"}`;
  return { rows, total, label };
}

function mdRowHtml(r, cat) {
  const chg = r.change;
  const chgHtml =
    chg === null || chg === undefined || isNaN(chg)
      ? `<span class="md-chg">—</span>`
      : `<span class="md-chg ${changeClass(chg)}">${formatChange(chg)}</span>`;
  // Only crypto gets Delta trade link (Delta doesn't offer metals/commodities/forex)
  const isCrypto = cat === "crypto" || !!r.deltaSymbol;
  const deltaUrl = isCrypto ? getDeltaTradeUrl(r.symbol, r.deltaSymbol) : null;
  const deltaLink = deltaUrl
    ? `<a href="${deltaUrl}" target="_blank" rel="noopener" class="md-delta-link" title="Trade ${r.symbol} on Delta India" aria-label="Trade ${r.symbol} on Delta India" onclick="event.stopPropagation()">Trade ↗</a>`
    : "";
  if (deltaUrl) {
    return `<div class="md-row-wrap" role="listitem">
      <button type="button" class="md-row" data-symbol="${r.symbol}">
        <span class="md-sym">${r.symbol}</span>
        <span class="md-name">${r.name || ""}</span>
        <span class="md-price">${mdPrice(r.price)}</span>
        ${chgHtml}
      </button>
      ${deltaLink}
    </div>`;
  }
  return `<button type="button" class="md-row" data-symbol="${r.symbol}" role="listitem">
      <span class="md-sym">${r.symbol}</span>
      <span class="md-name">${r.name || ""}</span>
      <span class="md-price">${mdPrice(r.price)}</span>
      ${chgHtml}
    </button>`;
}

function paintAssetRows(listEl, countEl, rows, label, cat) {
  if (countEl) countEl.textContent = label;
  if (!report) {
    if (listEl) listEl.innerHTML = `<p class="empty">Loading market data…</p>`;
    return [];
  }
  if (listEl) {
    listEl.innerHTML = rows.length
      ? rows.map((r) => mdRowHtml(r, cat)).join("")
      : `<p class="empty">No matches.</p>`;
  }
  return rows;
}

function renderSnapBrowser() {
  if (!els.snapList) return;
  els.snapTabs.forEach((btn) => {
    const isActive = btn.dataset.snapcat === snapCat;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-selected", String(isActive));
  });
  els.snapFilters.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.snapfilter === snapFilter);
  });
  const tools = document.getElementById("snap-crypto-tools");
  if (tools) tools.hidden = snapCat !== "crypto";
  if (els.snapSearch && document.activeElement !== els.snapSearch) {
    els.snapSearch.value = snapQuery;
  }
  renderSnapList();
}

function renderSnapList() {
  if (!els.snapList) return;
  let rows;
  let label;
  if (snapCat === "crypto") {
    const result = mdCryptoRows(snapQuery, snapFilter);
    rows = result.rows;
    label = result.label;
  } else {
    rows = mdCategoryAssets(snapCat);
    label = `${rows.length} asset${rows.length === 1 ? "" : "s"}`;
  }
  snapLastRows = paintAssetRows(els.snapList, els.snapCount, rows, label, snapCat);
}

function renderSnapshot() {
  renderSnapBrowser();
}

function renderMdList() {
  if (!els.mdList) return;
  let rows;
  let label;
  if (mdCat === "crypto") {
    const result = mdCryptoRows();
    rows = result.rows;
    label = result.label;
  } else {
    rows = mdCategoryAssets(mdCat);
    label = `${rows.length} asset${rows.length === 1 ? "" : "s"}`;
  }
  mdLastRows = paintAssetRows(els.mdList, els.mdCount, rows, label, mdCat);
}

function renderMarketsDropdown() {
  if (!els.marketsDropdown) return;
  els.mdCats.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.cat === mdCat);
  });
  els.mdCFilters.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.cfilter === mdCryptoFilter);
  });
  const tools = document.getElementById("md-crypto-tools");
  if (tools) tools.hidden = mdCat !== "crypto";
  if (els.mdSearch && document.activeElement !== els.mdSearch) {
    els.mdSearch.value = mdQuery;
  }
  renderMdList();
}

function setMarketsOpen(open) {
  if (!els.marketsDropdown || !els.marketsBtn) return;
  mdOpen = open;
  els.marketsDropdown.hidden = !open;
  els.marketsBtn.setAttribute("aria-expanded", String(open));
  if (open) renderMarketsDropdown();
}

// Validated 2026-09-14 against TradingView scanner API. TVC:USOIL/TVC:UKOIL
// are delisted and NYMEX/COMEX continuous futures trigger a licensing
// popup in the embeddable widget, so oil/copper use NYSE Arca ETF proxies.
const COMMODITY_TV = {
  WTI: "AMEX:USO",
  BRENT: "AMEX:BNO",
  NATGAS: "OANDA:NATGASUSD",
  COPPER: "AMEX:CPER",
  PLAT: "TVC:PLATINUM",
};

// OANDA does not list every pair (e.g. USDCNY has no TradingView symbol;
// USDINR only exists as FX:USDINR).
const FOREX_TV_OVERRIDES = {
  USDINR: "FX:USDINR",
  USDCNY: null,
};

function mdChartSymbol(symbol, cat) {
  if (!report || !symbol) return null;
  // 1. Explicit overview mapping (majors + metals) — unchanged behavior.
  const known = [...(report.markets || []), ...(report.metals || [])]
    .find((m) => m.symbol === symbol);
  if (known) return getChartSymbol(known);
  // 2. Commodities table (also covers metals like PLAT).
  if (COMMODITY_TV[symbol]) return COMMODITY_TV[symbol];
  // 3. Forex pairs (default OANDA spot CFDs, all validated except overrides).
  if (cat === "forex") {
    if (symbol in FOREX_TV_OVERRIDES) return FOREX_TV_OVERRIDES[symbol];
    return `OANDA:${symbol}`;
  }
  // 4. Validated Binance spot symbol from the backend (never guessed).
  const coin = (report.crypto_full || []).find((c) => c.symbol === symbol);
  if (coin) return coin.chart_symbol || null;
  return null;
}

function isAssetOpen() {
  return !!(els.assetModal && !els.assetModal.hidden);
}

function closeAssetDetail() {
  if (els.assetModal) els.assetModal.hidden = true;
}

function assetDetailHtml(r, cat) {
  const catLabel = { crypto: "Crypto", metals: "Metals", commodities: "Commodities", forex: "Forex" }[cat] || cat;
  const chg = r.change;
  const chgHtml =
    chg === null || chg === undefined || isNaN(chg)
      ? `<span class="asset-chg">—</span>`
      : `<span class="asset-chg ${changeClass(chg)}">${formatChange(chg)} 24h</span>`;
  const statRow = (label, value) =>
    value
      ? `<div class="asset-stat"><span class="asset-stat-label">${label}</span><span class="asset-stat-value">${value}</span></div>`
      : "";
  return `
    <p class="asset-cat">${catLabel}</p>
    <h2 id="asset-symbol" class="asset-symbol">${r.symbol}</h2>
    <p class="asset-name">${r.name || ""}</p>
    <div class="asset-price-row">
      <span class="asset-price">${mdPrice(r.price)}</span>
      ${chgHtml}
    </div>
    <div class="asset-stats">
      ${statRow("Volume", r.volume ? formatCompact(r.volume) : "")}
      ${statRow("Market Cap", r.mcap ? formatCompact(r.mcap) : "")}
    </div>`;
}

function openAssetDetail(symbol, rows = mdLastRows, cat = mdCat) {
  const hit = rows.find((r) => r.symbol === symbol);
  if (!hit || !els.assetModal || !els.assetBody) return;
  els.assetBody.innerHTML = assetDetailHtml(hit, cat);
  const tv = mdChartSymbol(symbol, cat);
  if (els.assetChartBtn) {
    els.assetChartBtn.hidden = !tv;
    els.assetChartBtn.dataset.symbol = tv || "";
  }
  if (els.assetNoChart) {
    els.assetNoChart.hidden = !!tv;
  }
  setMarketsOpen(false);
  els.assetModal.hidden = false;
}

function toggleSidebar() {
  const isOpen = els.sidebar.classList.toggle("is-open");
  els.mobileOverlay.classList.toggle("is-visible", isOpen);
  els.hamburger.setAttribute("aria-expanded", isOpen);
  els.sidebarToggle.setAttribute("aria-expanded", isOpen);
}

function closeSidebar() {
  els.sidebar.classList.remove("is-open");
  els.mobileOverlay.classList.remove("is-visible");
  els.hamburger.setAttribute("aria-expanded", "false");
  els.sidebarToggle.setAttribute("aria-expanded", "false");
}

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    document.querySelectorAll(".filter").forEach((el) => {
      el.classList.toggle("is-active", el === button);
    });
    if (report) renderNews();
  });
});

els.search.addEventListener("input", () => {
  if (!report) return;
  renderNews();
  renderListings();
});

if (els.refreshBtn) {
  els.refreshBtn.addEventListener("click", () => {
    loadReport();
  });
}

if (els.chartControls) {
  els.chartControls.addEventListener("click", (event) => {
    const button = event.target.closest(".chart-btn");
    switchChart(button?.dataset.symbol);
  });
}

document.querySelectorAll(".chart-tf-btn").forEach((btn) => {
  btn.addEventListener("click", () => setTimeframe(btn.dataset.tf));
});

els.navItems.forEach((item) => {
  item.addEventListener("click", (event) => {
    const view = event.currentTarget.dataset.view;
    if (view === "dashboard" || view === "news" || view === "scanner" || view === "positions" || view === "orders" || view === "journal" || view === "risk" || view === "settings" || view === "ai-analysis") {
      switchView(view);
      closeSidebar();
    } else if (view === "execute-trade") {
      openTradeModal();
      closeSidebar();
    } else {
      showComingSoon(view);
      closeSidebar();
    }
  });
});

els.aiTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    switchAiTab(tab.dataset.tab);
  });
});

(els.aiFullTabs || document.querySelectorAll(".ai-full-panel .ai-tab")).forEach((tab) => {
  tab.addEventListener("click", () => {
    switchAiFullTab(tab.dataset.fulltab);
  });
});

if (els.marketsBtn) {
  els.marketsBtn.addEventListener("click", () => {
    setMarketsOpen(!mdOpen);
  });
}

els.mdCats.forEach((btn) => {
  btn.addEventListener("click", () => {
    mdCat = btn.dataset.cat;
    renderMarketsDropdown();
  });
});

els.mdCFilters.forEach((btn) => {
  btn.addEventListener("click", () => {
    mdCryptoFilter = btn.dataset.cfilter;
    renderMarketsDropdown();
  });
});

if (els.mdSearch) {
  els.mdSearch.addEventListener("input", (event) => {
    mdQuery = event.target.value;
    renderMdList();
  });
}

if (els.mdList) {
  els.mdList.addEventListener("click", (event) => {
    const row = event.target.closest(".md-row");
    if (!row) return;
    const hit = mdLastRows.find((r) => r.symbol === row.dataset.symbol);
    console.log("[markets] selected", {
      category: mdCat,
      symbol: row.dataset.symbol,
      name: hit ? hit.name : null,
      price: hit ? hit.price : null,
    });
    openAssetDetail(row.dataset.symbol);
  });
}

els.snapTabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    snapCat = btn.dataset.snapcat;
    renderSnapBrowser();
  });
});

const snapshotToggle = document.getElementById("snapshot-toggle");
const snapshotPanel = document.querySelector(".snapshot-panel");
if (snapshotToggle && snapshotPanel) {
  snapshotToggle.addEventListener("click", () => {
    const isCollapsed = snapshotPanel.classList.toggle("is-collapsed");
    snapshotToggle.setAttribute("aria-expanded", String(!isCollapsed));
  });
}

els.snapFilters.forEach((btn) => {
  btn.addEventListener("click", () => {
    snapFilter = btn.dataset.snapfilter;
    renderSnapBrowser();
  });
});

if (els.snapSearch) {
  els.snapSearch.addEventListener("input", (event) => {
    snapQuery = event.target.value;
    renderSnapList();
  });
}

if (els.snapList) {
  els.snapList.addEventListener("click", (event) => {
    const row = event.target.closest(".md-row");
    if (!row) return;
    const hit = snapLastRows.find((r) => r.symbol === row.dataset.symbol);
    console.log("[snapshot] selected", {
      category: snapCat,
      symbol: row.dataset.symbol,
      name: hit ? hit.name : null,
      price: hit ? hit.price : null,
    });
    openAssetDetail(row.dataset.symbol, snapLastRows, snapCat);
  });
}

document.addEventListener("click", (event) => {
  if (!mdOpen) return;
  if (event.target.closest(".markets-menu")) return;
  setMarketsOpen(false);
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (isTradeOpen()) {
    closeTradeModal();
    return;
  }
  if (isAssetOpen()) {
    closeAssetDetail();
    return;
  }
  if (mdOpen) setMarketsOpen(false);
});

if (els.tradeClose) {
  els.tradeClose.addEventListener("click", closeTradeModal);
}

if (els.tradeModal) {
  els.tradeModal.addEventListener("click", (e) => {
    if (e.target === els.tradeModal) closeTradeModal();
  });
}

if (els.tradeSymbol) {
  els.tradeSymbol.addEventListener("change", () => {
    setTradeError(null);
    refreshTradePrice();
  });
}

if (els.tradeLong) {
  els.tradeLong.addEventListener("click", () => setTradeSide("LONG"));
}

if (els.tradeShort) {
  els.tradeShort.addEventListener("click", () => setTradeSide("SHORT"));
}

if (els.tradeAmount) {
  els.tradeAmount.addEventListener("input", () => {
    setTradeError(null);
    refreshTradePrice();
  });
}

if (els.tradePlace) {
  els.tradePlace.addEventListener("click", submitTrade);
}

if (els.assetClose) {
  els.assetClose.addEventListener("click", closeAssetDetail);
}

if (els.assetModal) {
  els.assetModal.addEventListener("click", (e) => {
    if (e.target === els.assetModal) closeAssetDetail();
  });
}

if (els.assetChartBtn) {
  els.assetChartBtn.addEventListener("click", () => {
    const tvSymbol = els.assetChartBtn.dataset.symbol;
    if (!tvSymbol) return;
    closeAssetDetail();
    if (mdOpen) setMarketsOpen(false);
    switchChart(tvSymbol);
    const chartPanel = document.querySelector('[aria-labelledby="chart-heading"]');
    if (chartPanel) {
      const rect = chartPanel.getBoundingClientRect();
      if (rect.top < 0 || rect.bottom > window.innerHeight) {
        chartPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  });
}

if (els.positionsBody) {
  els.positionsBody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-close-position]");
    if (!button) return;
    closePosition(button.dataset.closePosition);
  });
}

if (els.hamburger) {
  els.hamburger.addEventListener("click", toggleSidebar);
}

if (els.mobileOverlay) {
  els.mobileOverlay.addEventListener("click", closeSidebar);
}

if (els.sidebarToggle) {
  els.sidebarToggle.addEventListener("click", toggleSidebar);
}

if (els.comingSoonClose) {
  els.comingSoonClose.addEventListener("click", hideComingSoon);
}

if (els.comingSoonModal) {
  els.comingSoonModal.addEventListener("click", (e) => {
    if (e.target === els.comingSoonModal) hideComingSoon();
  });
}

if (els.scrollToNews) {
  els.scrollToNews.addEventListener("click", () => {
    const newsSection = document.querySelector('[aria-labelledby="news-heading"]');
    if (newsSection) {
      newsSection.scrollIntoView({ behavior: "smooth" });
    }
  });
}
const aiFullScrollBtn = els.aiFullScrollToNews || document.getElementById("ai-full-scroll-to-news");
if (aiFullScrollBtn) {
  aiFullScrollBtn.addEventListener("click", () => {
    const newsSection = document.querySelector('[aria-labelledby="news-heading"]');
    if (newsSection) newsSection.scrollIntoView({ behavior: "smooth" });
  });
}

if (els.timezoneSelect) {
  els.timezoneSelect.value = activeTimezone;
  els.timezoneSelect.addEventListener("change", (event) => setTimezone(event.target.value));
}
if (els.settingsTimezone) {
  els.settingsTimezone.value = activeTimezone;
  els.settingsTimezone.addEventListener("change", (event) => setTimezone(event.target.value));
}

applyTheme(activeTheme);
syncSettingsDisplay();
if (els.themeToggle) {
  els.themeToggle.addEventListener("click", () => {
    applyTheme(activeTheme === "dark" ? "light" : "dark");
  });
}
if (els.settingsThemeToggle) {
  els.settingsThemeToggle.addEventListener("click", () => {
    applyTheme(activeTheme === "dark" ? "light" : "dark");
  });
}
if (els.settingsReset) {
  els.settingsReset.addEventListener("click", resetPaperAccount);
}

async function loadReport() {
  if (isLoading) return;
  
  setLoading(true);
  try {
    let response = await fetch(REPORT_URL);
    if (!response.ok) throw new Error(`Primary fetch failed (${response.status})`);
    report = await response.json();
    renderReport();
  } catch (primaryError) {
    console.warn("Primary report fetch failed, trying fallback:", primaryError);
    try {
      const fallbackResponse = await fetch(REPORT_FALLBACK_URL);
      if (!fallbackResponse.ok) throw new Error(`Could not load report (${fallbackResponse.status})`);
      report = await fallbackResponse.json();
      renderReport();
    } catch (fallbackError) {
      showError(
        `${fallbackError.message}. Make sure data/latest-report.json has been generated.`
      );
    }
  } finally {
    setLoading(false);
  }
}

loadReport();
startReportPolling();
startClock();
startCountdown();
connectDelta();
renderPaperBalance();
renderPositions();
renderSettings();

if (els.paperReset) {
  els.paperReset.addEventListener("click", resetPaperAccount);
}

window.addEventListener("storage", (event) => {
  if (!event || event.key === null || event.key === PAPER_KEY) {
    renderPaperBalance();
    renderPositions();
  }
});
const API_URL = "/api/report";

const els = {
  updatedAt: document.getElementById("updated-at"),
  updatedRelative: document.getElementById("updated-relative"),
  markets: document.getElementById("markets"),
  summary: document.getElementById("summary"),
  watch: document.getElementById("watch-list"),
  news: document.getElementById("news-list"),
  listings: document.getElementById("listings-body"),
  search: document.getElementById("search"),
  status: document.getElementById("status"),
  aiMorningSummary: document.getElementById("ai-morning-summary"),
  aiWatchList: document.getElementById("ai-watch-list"),
  marketSentiment: document.getElementById("market-sentiment"),
  trendingList: document.getElementById("trending-list"),
  refreshBtn: document.getElementById("refresh-btn"),
  chartContainer: document.getElementById("tradingview-widget"),
};

let report = null;
let activeFilter = "All";
let currentChartSymbol = "BTCUSD";
let isLoading = false;

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
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(date);
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

function matchesQuery(text, query) {
  return text.toLowerCase().includes(query);
}

function renderMarkets(markets) {
  els.markets.innerHTML = markets
    .map(
      (m) => `
      <article class="market-card">
        <div class="market-top">
          <span class="market-symbol">${m.symbol}</span>
          <span class="market-name">${m.name}</span>
        </div>
        <p class="market-price">${formatUsd(m.price)}</p>
        <p class="change ${changeClass(m.change_24h)}">${formatChange(m.change_24h)} 24h</p>
        <div class="market-stats">
          <span>Vol ${formatCompact(m.volume)}</span>
          <span>MCap ${formatCompact(m.market_cap)}</span>
        </div>
      </article>`
    )
    .join("");
}

function renderWatch(items) {
  els.watch.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function renderAiBriefing(aiBriefing) {
  if (!aiBriefing) {
    els.aiMorningSummary.textContent = "AI briefing not available";
    els.aiWatchList.innerHTML = "<li>No AI watch items available</li>";
    els.marketSentiment.textContent = "Unknown";
    els.marketSentiment.className = "sentiment-badge sentiment-unknown";
    return;
  }

  els.aiMorningSummary.textContent = aiBriefing.morning_summary || "AI briefing unavailable";
  
  const sentiment = aiBriefing.market_sentiment || "unknown";
  els.marketSentiment.textContent = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
  els.marketSentiment.className = `sentiment-badge sentiment-${sentiment}`;

  const watchItems = aiBriefing.things_to_watch || [];
  if (watchItems.length === 0) {
    els.aiWatchList.innerHTML = "<li>No watch items available</li>";
  } else {
    els.aiWatchList.innerHTML = watchItems
      .map((item) => `<li>${item}</li>`)
      .join("");
  }
}

function renderTrending(trendingCoins) {
  if (!trendingCoins || trendingCoins.length === 0) {
    els.trendingList.innerHTML = `<p class="empty">No trending data available</p>`;
    return;
  }

  els.trendingList.innerHTML = trendingCoins
    .map(
      (coin) => `
      <div class="trending-item">
        <div class="trending-header">
          <span class="trending-symbol">${coin.symbol}</span>
          <span class="trending-name">${coin.name}</span>
        </div>
        <div class="trending-metrics">
          <span class="trending-price">${formatUsd(coin.price)}</span>
          <span class="change ${changeClass(coin.change_24h)}">${formatChange(coin.change_24h)}</span>
          <span class="trending-volume">Vol ${formatCompact(coin.volume)}</span>
        </div>
        <div class="trending-score">
          <span class="score-label">Trend Score:</span>
          <span class="score-value">${coin.trending_score}</span>
        </div>
      </div>`
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
      interval: "D",
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      toolbar_bg: "#1c1a15",
      enable_publishing: false,
      allow_symbol_change: true,
      container_id: "tradingview-widget",
      hide_side_toolbar: false
    });
  }
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

function renderReport() {
  els.updatedAt.textContent = formatTime(report.generated_at);
  els.updatedRelative.textContent = relativeTime(report.generated_at);
  els.summary.textContent = report.summary;
  renderMarkets(report.markets);
  renderWatch(report.watch);
  renderAiBriefing(report.ai_briefing);
  renderTrending(report.trending);
  renderNews();
  renderListings();
  
  // Initialize TradingView chart after data loads
  if (!currentChartSymbol) {
    initTradingView("BTCUSD");
  }
}

function showError(message) {
  els.status.hidden = false;
  els.status.textContent = message;
  els.summary.textContent = "Report unavailable.";
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

// Refresh button handler
if (els.refreshBtn) {
  els.refreshBtn.addEventListener("click", () => {
    loadReport();
  });
}

// Chart symbol switcher
document.querySelectorAll(".chart-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const symbol = button.dataset.symbol;
    if (symbol && symbol !== currentChartSymbol) {
      currentChartSymbol = symbol;
      
      // Update active state
      document.querySelectorAll(".chart-btn").forEach((btn) => {
        btn.classList.toggle("is-active", btn === button);
      });
      
      // Reload chart with new symbol
      initTradingView(symbol);
    }
  });
});

async function loadReport() {
  if (isLoading) return;
  
  setLoading(true);
  try {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error(`Could not load report (${response.status})`);
    report = await response.json();
    renderReport();
  } catch (error) {
    showError(
      `${error.message}. Make sure the backend server is running (py -3 serve.py).`
    );
  } finally {
    setLoading(false);
  }
}

loadReport();

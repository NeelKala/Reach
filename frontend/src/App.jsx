import { useRef, useState } from "react";
import "./App.css";

const sampleHoldings = [
  { company: "Microsoft", ticker: "MSFT", sector: "Technology", weight: 24, region: "North America" },
  { company: "Amazon", ticker: "AMZN", sector: "Technology", weight: 20, region: "North America" },
  { company: "Nestle", ticker: "NESN", sector: "Consumer Goods", weight: 18, region: "Europe" },
  { company: "Toyota", ticker: "TM", sector: "Automotive", weight: 16, region: "Asia Pacific" },
  { company: "Maersk", ticker: "MAERSK", sector: "Logistics", weight: 12, region: "Europe" },
  { company: "Shell", ticker: "SHEL", sector: "Energy", weight: 10, region: "Europe" },
];

const infrastructureHoldings = [
  { company: "NVIDIA", ticker: "NVDA", sector: "Semiconductors", weight: 24, region: "North America" },
  { company: "TSMC", ticker: "TSM", sector: "Semiconductors", weight: 22, region: "Asia Pacific" },
  { company: "CATL", ticker: "300750", sector: "Battery Manufacturing", weight: 18, region: "Asia Pacific" },
  { company: "Rio Tinto", ticker: "RIO", sector: "Mining", weight: 15, region: "Global" },
  { company: "A.P. Moller–Maersk", ticker: "MAERSK", sector: "Logistics", weight: 12, region: "Europe" },
  { company: "Schneider Electric", ticker: "SU", sector: "Electrical Equipment", weight: 9, region: "Europe" },
];

const demoPortfolios = [
  {
    name: "Global Resilience Portfolio",
    summary: "Technology, consumer goods, automotive, logistics and energy.",
    holdings: sampleHoldings,
    fileName: "global_resilience_sample.csv",
  },
  {
    name: "Critical Infrastructure Portfolio",
    summary: "Semiconductors, batteries, mining, shipping and electrical equipment.",
    holdings: infrastructureHoldings,
    fileName: "critical_infrastructure_sample.csv",
  },
];

const hazards = [
  { name: "Riverine flood", detail: "RCP8.5 · 1-in-100y", color: "#ff4d3d" },
  { name: "Extreme heat", detail: "+2.4°C by 2050", color: "#ff6b4a" },
  { name: "Drought", detail: "SPEI < -1.5", color: "#ff493b" },
  { name: "Tropical cyclone", detail: "Category 4+", color: "#ff5948" },
];

const graphNodes = [
  { id: "hazard", x: 5, y: 57, label: "Drought", type: "hazard", color: "#ff493b", r: 12 },
  { id: "flood", x: 5, y: 17, label: "Riverine flood", type: "hazard", color: "#ff493b", r: 5 },
  { id: "heat", x: 5, y: 36, label: "Extreme heat", type: "hazard", color: "#ff493b", r: 5 },
  { id: "cyclone", x: 5, y: 77, label: "Tropical cyclone", type: "hazard", color: "#ff493b", r: 5 },
  { id: "h1", x: 17, y: 13, label: "Mekong Delta, VN", type: "region", color: "#4cc8ef", r: 5 },
  { id: "h2", x: 17, y: 29, label: "Gujarat, IN", type: "region", color: "#4cc8ef", r: 5 },
  { id: "h3", x: 17, y: 53, label: "Gulf Coast, US", type: "region", color: "#4cc8ef", r: 5 },
  { id: "h4", x: 17, y: 68, label: "Hsinchu, TW", type: "region", color: "#4cc8ef", r: 10 },
  { id: "h5", x: 17, y: 82, label: "Atacama, CL", type: "region", color: "#4cc8ef", r: 9 },
  { id: "f1", x: 29, y: 13, label: "Semiconductor fab", type: "facility", color: "#b9a5ff", r: 9 },
  { id: "f2", x: 29, y: 29, label: "Petrochem refinery", type: "facility", color: "#b9a5ff", r: 5 },
  { id: "f3", x: 29, y: 36, label: "Textile mill cluster", type: "facility", color: "#b9a5ff", r: 5 },
  { id: "f4", x: 29, y: 54, label: "Chemical plant", type: "facility", color: "#b9a5ff", r: 9 },
  { id: "f5", x: 29, y: 68, label: "Lithium brine site", type: "facility", color: "#b9a5ff", r: 9 },
  { id: "f6", x: 29, y: 82, label: "Rice processing hub", type: "facility", color: "#b9a5ff", r: 5 },
  { id: "t1", x: 41, y: 32, label: "Port of Houston", type: "transport", color: "#40d8d6", r: 5 },
  { id: "t2", x: 41, y: 57, label: "Taiwan Strait lanes", type: "transport", color: "#40d8d6", r: 9 },
  { id: "t3", x: 41, y: 79, label: "Mundra Port", type: "transport", color: "#40d8d6", r: 5 },
  { id: "c1", x: 53, y: 13, label: "Advanced chips", type: "commodity", color: "#ffb526", r: 10 },
  { id: "c2", x: 53, y: 28, label: "Polyethylene", type: "commodity", color: "#ffb526", r: 5 },
  { id: "c3", x: 53, y: 41, label: "Cotton yarn", type: "commodity", color: "#ffb526", r: 5 },
  { id: "c4", x: 53, y: 54, label: "Lithium carbonate", type: "commodity", color: "#ffb526", r: 10 },
  { id: "c5", x: 53, y: 68, label: "Rice", type: "commodity", color: "#ffb526", r: 5 },
  { id: "c6", x: 53, y: 82, label: "Ammonia", type: "commodity", color: "#ffb526", r: 10 },
  { id: "s1", x: 65, y: 14, label: "Foundry Tier-1", type: "supplier", color: "#e987c8", r: 8 },
  { id: "s2", x: 65, y: 32, label: "Packaging Co.", type: "supplier", color: "#e987c8", r: 5 },
  { id: "s3", x: 65, y: 45, label: "Garment OEM", type: "supplier", color: "#e987c8", r: 5 },
  { id: "s4", x: 65, y: 61, label: "Battery cell maker", type: "supplier", color: "#e987c8", r: 8 },
  { id: "s5", x: 65, y: 81, label: "Food ingredients", type: "supplier", color: "#e987c8", r: 7 },
  { id: "p1", x: 77, y: 14, label: "Consumer Tech Inc.", type: "company", color: "#b6e84f", r: 8 },
  { id: "p2", x: 77, y: 27, label: "EV Motors AG", type: "company", color: "#b6e84f", r: 8 },
  { id: "p3", x: 77, y: 42, label: "Global Apparel", type: "company", color: "#b6e84f", r: 5 },
  { id: "p4", x: 77, y: 61, label: "Staples Foods plc", type: "company", color: "#b6e84f", r: 8 },
  { id: "p5", x: 77, y: 81, label: "Specialty Chem SA", type: "company", color: "#b6e84f", r: 8 },
  { id: "e1", x: 90, y: 20, label: "Equity sleeve", type: "exposure", color: "#e6e9d9", r: 7 },
  { id: "e2", x: 90, y: 43, label: "IG credit", type: "exposure", color: "#e6e9d9", r: 7 },
  { id: "e3", x: 90, y: 71, label: "Lender syndicate", type: "exposure", color: "#e6e9d9", r: 7 },
];

const graphEdges = [
  ["hazard", "h4", "#ff493b"], ["hazard", "f2", "#ff493b"], ["hazard", "h5", "#ff493b"],
  ["h4", "f1", "#b6e84f"], ["f1", "c1", "#b6e84f"], ["c1", "s1", "#b6e84f"], ["s1", "p1", "#b6e84f"], ["p1", "e1", "#57d78b"],
  ["h2", "f4", "#ffb526"], ["f4", "t2", "#ffb526"], ["t2", "c4", "#ffb526"], ["c4", "s4", "#ffb526"], ["s4", "p2", "#57d78b"], ["p2", "e2", "#57d78b"],
  ["h5", "f5", "#ffb526"], ["f5", "t3", "#ffb526"], ["t3", "c6", "#ffb526"], ["c6", "s5", "#57d78b"], ["s5", "p5", "#57d78b"], ["p5", "e3", "#57d78b"],
  ["h3", "f2", "#ff493b"], ["f2", "c2", "#ffb526"], ["c2", "s2", "#ffb526"], ["s2", "p3", "#57d78b"], ["p3", "e1", "#57d78b"],
  ["f4", "c6", "#ffb526"], ["c1", "s2", "#ffb526"], ["s3", "p3", "#57d78b"], ["s4", "p4", "#57d78b"], ["p4", "e2", "#57d78b"],
  ["f6", "c5", "#ffb526"], ["c5", "s5", "#ffb526"], ["s5", "p4", "#57d78b"], ["h1", "f1", "#b6e84f"], ["h3", "t1", "#4cc8ef"],
];

const exposureCompanies = [
  { name: "Consumer Tech Inc.", score: 29, weight: "7.2%", order: "2nd-order", hops: 5 },
  { name: "EV Motors AG", score: 24, weight: "5.1%", order: "2nd-order", hops: 5 },
  { name: "Specialty Chem SA", score: 24, weight: "2.9%", order: "1st-order", hops: 4 },
  { name: "Staples Foods plc", score: 9, weight: "4.4%", order: "2nd-order", hops: 5 },
  { name: "Global Apparel", score: 0, weight: "3.8%", order: "unaffected", hops: 0 },
];

const legend = [
  ["Climate hazard", "#ff493b"], ["Region", "#4cc8ef"], ["Facility", "#b9a5ff"],
  ["Transport route", "#40d8d6"], ["Commodity", "#ffb526"], ["Supplier", "#e987c8"],
  ["Portfolio company", "#b6e84f"], ["Financial exposure", "#e6e9d9"],
];

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((v) => v.trim().toLowerCase().replace(/^"|"$/g, ""));
  return lines.slice(1).map((line, index) => {
    const cells = line.split(",").map((v) => v.trim().replace(/^"|"$/g, ""));
    const get = (...names) => {
      const pos = headers.findIndex((h) => names.includes(h));
      return pos >= 0 ? cells[pos] || "" : "";
    };
    return {
      company: get("company", "company_name", "name") || `Company ${index + 1}`,
      ticker: get("ticker", "symbol") || "—",
      sector: get("sector", "industry") || "Unspecified",
      weight: Number(get("weight", "portfolio_weight", "allocation")) || 0,
      region: get("region", "country", "geography") || "Unspecified",
    };
  });
}

function NetworkGraph({ selectedHazard, shock, retention, selectedCompany, onSelectCompany }) {
  const activeColor = selectedHazard === "Drought" ? "#ff493b" : selectedHazard === "Extreme heat" ? "#ff9b43" : selectedHazard === "Riverine flood" ? "#4cc8ef" : "#b9a5ff";
  const nodeMap = Object.fromEntries(graphNodes.map((node) => [node.id, node]));
  const isCompany = (node) => node.type === "company";
  return (
    <div className="reach-graph-wrap">
      <div className="graph-column-labels">
        {["CLIMATE HAZARD", "REGION", "FACILITY", "TRANSPORT ROUTE", "COMMODITY", "SUPPLIER", "PORTFOLIO COMPANY", "FINANCIAL EXPOSURE"].map((label) => <span key={label}>{label}</span>)}
      </div>
      <svg className="reach-graph" viewBox="0 0 1000 510" role="img" aria-label="Illustrative climate exposure network graph">
        <g className="graph-grid">
          {Array.from({ length: 11 }, (_, i) => <line key={`v${i}`} x1={i * 100} y1="0" x2={i * 100} y2="510" />)}
          {Array.from({ length: 6 }, (_, i) => <line key={`h${i}`} x1="0" y1={i * 100} x2="1000" y2={i * 100} />)}
        </g>
        <g>
          {graphEdges.map(([from, to, color], i) => {
            const a = nodeMap[from], b = nodeMap[to];
            const x1 = a.x * 10, y1 = a.y * 5.05, x2 = b.x * 10, y2 = b.y * 5.05;
            const bend = (x2 - x1) * 0.48;
            const selectedPath = from === "hazard" || to === "hazard" || from === "h4" || to === "h4" || from === "f1" || to === "f1" || (selectedCompany && (a.label === selectedCompany || b.label === selectedCompany));
            return <path key={i} d={`M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`} stroke={selectedPath ? (from === "hazard" || to === "hazard" ? activeColor : color) : color} className={selectedPath ? "graph-edge active" : "graph-edge"} style={{ opacity: selectedPath ? Math.min(.95, .5 + shock * .45) : .14 + retention * .15 }} />;
          })}
        </g>
        {graphNodes.map((node) => {
          const selected = node.label === selectedCompany;
          const r = node.r + (node.type === "hazard" && node.id === "hazard" ? shock * 3 : 0);
          return <g key={node.id} className={`graph-node ${isCompany(node) ? "clickable" : ""} ${selected ? "selected" : ""}`} onClick={() => isCompany(node) && onSelectCompany(node.label)}>
            <circle cx={node.x * 10} cy={node.y * 5.05} r={r + 5} fill={node.color} opacity=".09" />
            <circle cx={node.x * 10} cy={node.y * 5.05} r={r} fill={node.color} fillOpacity={node.type === "hazard" ? ".95" : ".28"} stroke={node.color} strokeWidth={selected ? 3 : 1.6} />
            <text x={node.x * 10} y={node.y * 5.05 + r + 13} textAnchor="middle" className="graph-node-label">{node.label}</text>
          </g>;
        })}
      </svg>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("home");
  const [holdings, setHoldings] = useState([]);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [selectedHazard, setSelectedHazard] = useState("Drought");
  const [shock, setShock] = useState(0.8);
  const [retention, setRetention] = useState(0.85);
  const [selectedCompany, setSelectedCompany] = useState("Consumer Tech Inc.");
  const fileRef = useRef(null);

  function loadSamplePortfolio(portfolio = demoPortfolios[0]) {
    setHoldings(portfolio.holdings);
    setFileName(portfolio.fileName);
    setError("");
    setPage("dashboard");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function uploadFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Please choose a CSV file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const rows = parseCSV(String(reader.result || ""));
        if (!rows.length) {
          setError("No holdings found. Please check your CSV headers and rows.");
          return;
        }
        setHoldings(rows);
        setFileName(file.name);
        setError("");
        setPage("dashboard");
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch {
        setError("Unable to read this file. Please check the CSV format.");
      }
    };
    reader.onerror = () => setError("Unable to read the selected file.");
    reader.readAsText(file);
  }

  const totalWeight = holdings.reduce((sum, item) => sum + item.weight, 0);
  const displayedScore = Math.round(19 + shock * 8 + (retention - 0.5) * 9);
  const selectedDetails = exposureCompanies.find((company) => company.name === selectedCompany) || exposureCompanies[0];

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => setPage("home")} aria-label="Reach overview">
          <span className="brand-icon">◈</span>
          <span className="brand-name">REACH<span className="orange">.</span><small>CLIMATE INTELLIGENCE</small></span>
        </button>
        <nav className="navigation">
          <button className={page === "home" ? "nav-link active" : "nav-link"} onClick={() => setPage("home")}>Overview</button>
          <button className={page === "dashboard" ? "nav-link active" : "nav-link"} onClick={() => setPage("dashboard")}>Analytics</button>
          <span className="demo-status"><i /> DEMO ENVIRONMENT</span>
        </nav>
      </header>

      {page === "home" ? (
        <main className="landing">
          <section className="hero">
            <div className="eyebrow"><i /> CLIMATE RISK. CONNECTED.</div>
            <h1>See the risks<br />that <span>aren't visible.</span></h1>
            <p className="hero-copy">Climate risk doesn't stop at a company's front door. Discover how hazards travel through suppliers, logistics, commodities and regions to reveal hidden portfolio exposure.</p>
            <div className="hero-actions">
              <button className="primary-btn" onClick={() => document.getElementById("upload")?.scrollIntoView({ behavior: "smooth" })}>Analyse your portfolio <span>↗</span></button>
              <button className="secondary-btn" onClick={() => loadSamplePortfolio()}>Explore demo portfolio →</button>
            </div>
            <div className="hero-note">✳ &nbsp; A connected view of climate risk</div>
            <div className="network-card">
              <div className="network-heading"><span><i /> NETWORK PREVIEW</span><small>ILLUSTRATIVE GRAPH</small></div>
              <NetworkGraph selectedHazard={selectedHazard} shock={shock} retention={retention} selectedCompany={selectedCompany} onSelectCompany={setSelectedCompany} />
              <div className="network-legend"><span><i className="legend-company" /> Companies</span><span><i className="legend-region" /> Regions</span><span><i className="legend-supply" /> Supply chain</span><span><i className="legend-hazard" /> Climate hazards</span></div>
            </div>
          </section>
          <section className="portfolio-section" id="portfolios">
            <div className="portfolio-section-heading">
              <div><div className="section-kicker">01 / PORTFOLIOS</div><h2>Start with a portfolio.</h2><p className="section-copy">Explore a sample portfolio now, or upload your own holdings below.</p></div>
              <span className="portfolio-count">{String(demoPortfolios.length).padStart(2, "0")} SAMPLES</span>
            </div>
            <div className="portfolio-card-grid">
              {demoPortfolios.map((portfolio) => (
                <button className="portfolio-card" key={portfolio.name} onClick={() => loadSamplePortfolio(portfolio)}>
                  <div className="portfolio-card-top"><span className="portfolio-card-icon">◈</span><span className="portfolio-demo-tag">DEMO DATA</span></div>
                  <h3>{portfolio.name}</h3>
                  <p>{portfolio.summary}</p>
                  <div className="portfolio-card-meta"><span>{String(portfolio.holdings.length).padStart(2, "0")} holdings</span><span>Climate risk preview</span></div>
                  <span className="portfolio-card-action">Explore portfolio <b>↗</b></span>
                </button>
              ))}
            </div>
          </section>
          <section className="upload-section" id="upload">
            <div className="section-kicker">02 / GET STARTED</div>
            <h2>Your portfolio.<br /><span>A new perspective.</span></h2>
            <p className="section-copy">Upload your investment holdings to enter the Reach climate workspace.</p>
            <div className="upload-card">
              <div className="upload-icon">↑</div><h3>Upload portfolio data</h3><p>Start with a CSV file containing your investment holdings.</p>
              <button className={`upload-dropzone ${dragging ? "dragging" : ""}`} onClick={() => fileRef.current?.click()} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); uploadFile(event.dataTransfer.files?.[0]); }}>
                <span className="file-icon">▤</span><strong>Drop your CSV here or click to browse</strong><small>CSV format · Company, ticker, sector, weight, region</small>
              </button>
              <input ref={fileRef} type="file" accept=".csv,text/csv" hidden onChange={(event) => { uploadFile(event.target.files?.[0]); event.target.value = ""; }} />
              {error && <p className="error-message">{error}</p>}
              <div className="privacy-note">◈ &nbsp; Demo files are read locally in your browser.</div>
              <div className="upload-divider"><span>OR</span></div>
              <button className="demo-btn" onClick={() => loadSamplePortfolio()}>Use sample portfolio <span>→</span></button>
            </div>
          </section>
          <section className="feature-strip">
            <div><span>01</span><strong>Connect the dots</strong><p>Explore relationships beyond direct holdings.</p></div>
            <div><span>02</span><strong>Trace propagation</strong><p>Understand second- and third-order effects.</p></div>
            <div><span>03</span><strong>Reveal exposure</strong><p>Spot potential hidden portfolio dependencies.</p></div>
          </section>
        </main>
      ) : (
        <main className="graph-dashboard">
          <header className="graph-dashboard-header">
            <div><div className="graph-eyebrow">PORTFOLIO RISK LAB</div><h1>Climate Exposure Graph</h1><p className="graph-subtitle">{fileName || "Portfolio preview"} · {holdings.length} holdings loaded</p></div>
            <div className="headline-stats">
              <div><span>PORTFOLIO STRESS</span><strong className="stress-value">{displayedScore}.0<small>/100</small></strong></div>
              <div><span>NODES HIT</span><strong>22<small>/39</small></strong></div>
              <div><span>HIDDEN EXPOSURES</span><strong className="hidden-value">2</strong></div>
            </div>
          </header>

          <div className="graph-dashboard-grid">
            <aside className="graph-sidebar left-sidebar">
              <section className="graph-panel hazard-panel">
                <h2>HAZARD SCENARIO</h2>
                <div className="hazard-options">
                  {hazards.map((hazard) => <button key={hazard.name} className={`hazard-option ${selectedHazard === hazard.name ? "selected" : ""}`} onClick={() => setSelectedHazard(hazard.name)}><strong>{hazard.name}</strong><span>{hazard.detail}</span></button>)}
                </div>
                <label className="slider-label" htmlFor="shock-range"><span>Shock intensity</span><strong>{shock.toFixed(2)}</strong></label>
                <input id="shock-range" className="risk-slider" type="range" min="0" max="1" step="0.05" value={shock} onChange={(e) => setShock(Number(e.target.value))} />
                <label className="slider-label" htmlFor="retention-range"><span>Propagation retention / hop</span><strong>{retention.toFixed(2)}</strong></label>
                <input id="retention-range" className="risk-slider" type="range" min="0.5" max="1" step="0.05" value={retention} onChange={(e) => setRetention(Number(e.target.value))} />
                <div className="graph-legend"><h3>LEGEND</h3>{legend.map(([label, color]) => <div key={label}><i style={{ background: color }} />{label}</div>)}</div>
              </section>
            </aside>

            <section className="graph-panel main-graph-panel">
              <NetworkGraph selectedHazard={selectedHazard} shock={shock} retention={retention} selectedCompany={selectedCompany} onSelectCompany={setSelectedCompany} />
              <div className="graph-disclaimer">Illustrative network · Select a portfolio company node to inspect its path. Scores are demo values.</div>
            </section>

            <aside className="graph-sidebar right-sidebar">
              <section className="graph-panel company-panel">
                <h2>COMPANY EXPOSURE</h2>
                <div className="company-exposure-list">
                  {exposureCompanies.map((company) => <button key={company.name} className={`company-exposure ${selectedCompany === company.name ? "selected" : ""}`} onClick={() => setSelectedCompany(company.name)}>
                    <span className="company-score-line"><strong>{company.name}</strong><b>{company.score}</b></span>
                    <span className="company-bar"><i style={{ width: `${Math.max(0, company.score / 30 * 100)}%` }} /></span>
                    <span className="company-meta"><span>{company.weight} AUM</span><span>{company.order}{company.hops ? ` · ${company.hops} hops` : ""}</span></span>
                  </button>)}
                </div>
              </section>
              <section className="graph-panel contagion-panel">
                <h2>CONTAGION PATH</h2>
                <h3>{selectedCompany}</h3>
                <div className="path-step"><i style={{ background: "#ff493b" }} /><span>{selectedHazard}</span><small>hop 0</small></div>
                <div className="path-step"><i style={{ background: "#4cc8ef" }} /><span>Hsinchu, TW</span><small>hop 1</small></div>
                <div className="path-step"><i style={{ background: "#b9a5ff" }} /><span>Semiconductor fab</span><small>hop 2</small></div>
                <div className="path-step"><i style={{ background: "#ffb526" }} /><span>Advanced chips</span><small>hop 3</small></div>
                <div className="path-step"><i style={{ background: "#e987c8" }} /><span>Foundry Tier-1</span><small>hop 4</small></div>
                <div className="path-step"><i style={{ background: "#b6e84f" }} /><span>{selectedCompany}</span><small>hop 5</small></div>
                <div className="path-summary"><span>Selected exposure score</span><strong>{selectedDetails.score}/100</strong></div>
              </section>
              <section className="graph-panel portfolio-mini-panel">
                <h2>PORTFOLIO SNAPSHOT</h2>
                <div><span>Companies uploaded</span><strong>{holdings.length}</strong></div>
                <div><span>Portfolio weight entered</span><strong>{totalWeight.toFixed(1)}%</strong></div>
                <button className="back-overview-btn" onClick={() => setPage("home")}>← Back to overview</button>
              </section>
            </aside>
          </div>
          <p className="dashboard-disclaimer">Prototype only: climate scores, paths, and exposure values are illustrative demo data, not measured climate-risk estimates.</p>
        </main>
      )}
    </div>
  );
}

export default App;

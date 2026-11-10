
import { useCallback, useEffect, useState } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BriefcaseBusiness,
  Users,
  RefreshCw,
  ShieldCheck,
  Clock3,
  Search,
  CircleDot,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000/api";

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [cases, setCases] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [analysts, setAnalysts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");


  const loadData = useCallback(async () => {
    try {
      const [d, c, a, an] = await Promise.all([
        fetch(`${API}/dashboard`),
        fetch(`${API}/cases`),
        fetch(`${API}/alerts`),
        fetch(`${API}/analysts`),
      ]);

      if (![d, c, a, an].every((r) => r.ok)) {
        throw new Error("One or more API endpoints returned an error.");
      }

      const [dashboardData, caseData, alertData, analystData] =
        await Promise.all([d.json(), c.json(), a.json(), an.json()]);

      setDashboard(dashboardData);
      setCases(Array.isArray(caseData) ? caseData : caseData.items || caseData.cases || []);
      setAlerts(Array.isArray(alertData) ? alertData : alertData.items || alertData.alerts || []);
      setAnalysts(Array.isArray(analystData) ? analystData : analystData.items || analystData.analysts || []);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(loadData);
  }, [loadData]);

  const riskData = Object.entries(dashboard?.alert_risk_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );

  const priorityData = Object.entries(dashboard?.case_priority_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );

  const filteredCases = cases.filter((item) => {
    const id = String(item.case_id || item.id || "").toLowerCase();
    const status = String(item.case_status || item.status || "").toUpperCase();
    const priority = String(item.priority || "").toUpperCase();
    const matchesSearch = id.includes(search.toLowerCase());
    const matchesFilter = filter === "ALL" || priority === filter || status === filter;
    return matchesSearch && matchesFilter;
  });

  const priorityClass = (value) =>
    String(value || "MEDIUM").toLowerCase();

  const getAnalystName = (item) =>
    item.assigned_analyst_name ||
    item.analyst_name ||
    item.assigned_analyst_id ||
    item.analyst_id ||
    "Unassigned";

  const formatDate = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={23} /></div>
          <div>
            <h2>Risk<span>Lens</span></h2>
            <p>TRANSACTION INTELLIGENCE</p>
          </div>
        </div>

        <div className="side-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview"><Activity size={18} /> Overview</a>
        <a className="nav-item" href="#cases"><BriefcaseBusiness size={18} /> Case Management</a>
        <a className="nav-item" href="#alerts"><AlertTriangle size={18} /> Risk Alerts</a>
        <a className="nav-item" href="#analysts"><Users size={18} /> Analysts</a>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div><strong>System operational</strong><small>API connection</small></div>
          </div>
          <p>RiskLens · Version 1.0.0</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">RISK OPERATIONS / OVERVIEW</div>
            <h1>Transaction Risk Dashboard</h1>
            <p className="page-subtitle">Monitor suspicious activity and prioritize investigations.</p>
          </div>
          <button className="refresh-button" onClick={() => {
            setLoading(true);
            setError("");
            loadData();
          }}>
            <RefreshCw size={16} /> Refresh data
          </button>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            {error} Check that FastAPI is running on port 8000 and CORS allows port 5175.
            <button onClick={() => {
              setLoading(true);
              setError("");
              loadData();
            }}>Retry</button>
          </div>
        )}

        {loading && !dashboard ? (
          <div className="loading">Loading risk intelligence...</div>
        ) : (
          <>
            <section className="metrics-grid" id="overview">
              <MetricCard icon={<Activity />} label="Total transactions" value={dashboard?.total_transactions ?? 0} note="Transactions evaluated" />
              <MetricCard icon={<AlertTriangle />} label="Risk alerts" value={dashboard?.total_alerts ?? 0} note="Alerts generated" accent="orange" />
              <MetricCard icon={<BriefcaseBusiness />} label="Investigation cases" value={dashboard?.total_cases ?? 0} note="Cases created" accent="purple" />
              <MetricCard icon={<Users />} label="Active analysts" value={dashboard?.active_analysts ?? 0} note="Assigned to operations" accent="green" />
            </section>

            <section className="charts-grid">
              <div className="panel chart-panel">
                <div className="panel-heading">
                  <div><h3>Alert risk distribution</h3><p>Breakdown by risk level</p></div>
                  <span className="panel-icon"><AlertTriangle size={17} /></span>
                </div>
                {riskData.length ? (
                  <div className="chart-content">
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={58} outerRadius={85} paddingAngle={4}>
                          {riskData.map((entry) => <Cell key={entry.name} fill={entry.name === "HIGH" ? "#f97362" : entry.name === "CRITICAL" ? "#dc2626" : entry.name === "MEDIUM" ? "#eab65c" : "#39b98a"} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="chart-legend">
                      {riskData.map((item) => (
                        <div key={item.name}><span className={`legend-dot ${priorityClass(item.name)}`} />{item.name}<strong>{item.value}</strong></div>
                      ))}
                    </div>
                  </div>
                ) : <EmptyState text="No risk distribution available." />}
              </div>

              <div className="panel chart-panel">
                <div className="panel-heading">
                  <div><h3>Cases by priority</h3><p>Investigation workload</p></div>
                  <span className="panel-icon"><BriefcaseBusiness size={17} /></span>
                </div>
                {priorityData.length ? (
                  <ResponsiveContainer width="100%" height={245}>
                    <BarChart data={priorityData} margin={{ top: 15, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#263448" />
                      <XAxis dataKey="name" tick={{ fill: "#9aa9bc", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis allowDecimals={false} tick={{ fill: "#9aa9bc", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="value" name="Cases" fill="#7298f4" radius={[6, 6, 0, 0]} barSize={48} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <EmptyState text="No case priority data available." />}
              </div>
            </section>

            <section className="panel cases-panel" id="cases">
              <div className="panel-heading section-heading">
                <div><h3>Investigation cases</h3><p>Review and prioritize assigned cases</p></div>
                <span className="count-pill">{cases.length} total</span>
              </div>
              <div className="table-tools">
                <div className="search-box"><Search size={16} /><input placeholder="Search case ID..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
                <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                  <option value="ALL">All cases</option>
                  <option value="HIGH">High priority</option>
                  <option value="MEDIUM">Medium priority</option>
                  <option value="LOW">Low priority</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In progress</option>
                  <option value="ESCALATED">Escalated</option>
                  <option value="RESOLVED">Resolved</option>
                </select>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>CASE ID</th><th>PRIORITY</th><th>STATUS</th><th>ANALYST</th><th>CREATED</th></tr></thead>
                  <tbody>
                    {filteredCases.map((item, index) => (
                      <tr key={item.case_id || item.id || index}>
                        <td className="case-id">{item.case_id || item.id || "—"}</td>
                        <td><span className={`priority-badge ${priorityClass(item.priority)}`}>{item.priority || "—"}</span></td>
                        <td><span className="status-text"><CircleDot size={13} />{item.case_status || item.status || "—"}</span></td>
                        <td>{getAnalystName(item)}</td>
                        <td>{formatDate(item.created_at)}</td>
                      </tr>
                    ))}
                    {!filteredCases.length && <tr><td colSpan="5"><EmptyState text="No matching cases found." /></td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="bottom-grid">
              <div className="panel" id="alerts">
                <div className="panel-heading"><div><h3>Recent risk alerts</h3><p>Latest detected activity</p></div><span className="panel-icon"><AlertTriangle size={17} /></span></div>
                <div className="compact-list">
                  {alerts.slice(0, 7).map((item, index) => (
                    <div className="compact-row" key={item.alert_id || item.id || index}>
                      <span className={`alert-marker ${priorityClass(item.risk_level)}`} />
                      <div className="compact-main">
                        <strong>{item.alert_id || item.rule_name || `Alert ${index + 1}`}</strong>
                        <small>{item.transaction_id || item.description || item.rule_code || "Transaction risk detected"}</small>
                      </div>
                      <span className={`priority-badge ${priorityClass(item.risk_level)}`}>{item.risk_level || "—"}</span>
                    </div>
                  ))}
                  {!alerts.length && <EmptyState text="No alerts available." />}
                </div>
              </div>

              <div className="panel" id="analysts">
                <div className="panel-heading"><div><h3>Analyst workload</h3><p>Current case assignments</p></div><span className="panel-icon"><Users size={17} /></span></div>
                <div className="compact-list">
                  {analysts.map((item, index) => (
                    <div className="analyst-row" key={item.analyst_id || item.id || index}>
                      <div className="avatar">{(item.analyst_name || item.name || "A").slice(0, 1).toUpperCase()}</div>
                      <div className="compact-main"><strong>{item.analyst_name || item.name || item.analyst_id || "Analyst"}</strong><small>{item.role || "Risk Analyst"}</small></div>
                      <span className="workload"><BriefcaseBusiness size={13} /> {item.active_cases ?? item.workload ?? item.case_count ?? 0} cases</span>
                    </div>
                  ))}
                  {!analysts.length && <EmptyState text="No analyst data available." />}
                </div>
              </div>
            </section>

            <footer className="footer">
              <span><span className="status-dot" /> Connected to PostgreSQL via FastAPI</span>
              <span><Clock3 size={13} /> Rule-based risk monitoring · Demo environment</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

function MetricCard({ icon, label, value, note, accent = "blue" }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${accent}`}>{icon}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{Number(value).toLocaleString()}</div>
      <div className="metric-note"><ArrowUpRight size={14} /> {note}</div>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>;
}

export default App;

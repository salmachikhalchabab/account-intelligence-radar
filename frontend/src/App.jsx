import { useState } from "react"
import { useAuth } from "./AuthContext"
import { useToast } from "./ToastContext"
import AuthPage from "./pages/AuthPage"
import Dashboard from "./pages/Dashboard"
import CompanyMode from "./pages/CompanyMode"
import GeographyMode from "./pages/GeographyMode"
import ReportView from "./pages/ReportView"
import "./App.css"

export default function App() {
  const { user, logout, loading } = useAuth()
  const toast = useToast()
  const [page, setPage] = useState("dashboard")
  const [selectedReport, setSelectedReport] = useState(null)

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh", background: "var(--bg)",
        display: "flex", alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: 16
      }}>
        <div className="spinner spinner-lg" />
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "var(--text3)", letterSpacing: "0.1em" }}>
          LOADING...
        </div>
      </div>
    )
  }

  if (!user) return <AuthPage />

  const navigate = (p, data = null) => {
    setSelectedReport(data)
    setPage(p)
  }

  const handleLogout = () => {
    logout()
    toast.info("Signed out", "You have been signed out successfully.")
  }

  const navItems = [
    { id: "dashboard", icon: "⬡", label: "Dashboard" },
    { id: "company",   icon: "◎", label: "Company Mode" },
    { id: "geography", icon: "◈", label: "Geography Mode" },
  ]

  return (
    <div className="app">
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-mark">◈</div>
          <div className="logo-text">
            <div className="logo-name">Intelligence Radar</div>
            <div className="logo-tagline">by Averroa</div>
          </div>
        </div>

        <div className="nav-section">
          <div className="nav-label" style={{ marginBottom: 8 }}>Navigation</div>
          {navItems.map(({ id, icon, label }) => (
            <button
              key={id}
              className={`nav-link ${page === id || (page === "report" && id === "dashboard") ? "active" : ""}`}
              onClick={() => navigate(id)}
            >
              <span className="nav-icon">{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">
              {user.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="user-info">
              <div className="user-name">{user.username}</div>

            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout}
            style={{ width: "100%", justifyContent: "center", color: "var(--text3)", fontSize: 12 }}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main */}
      <main className="main-content">
        {page === "dashboard" && <Dashboard onViewReport={(r) => navigate("report", r)} />}
        {page === "company"   && <CompanyMode />}
        {page === "geography" && <GeographyMode />}
        {page === "report"    && <ReportView report={selectedReport} onBack={() => navigate("dashboard")} />}
      </main>
    </div>
  )
}

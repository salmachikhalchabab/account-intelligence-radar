import { useState, useEffect } from "react"
import { useAuth, API_URL } from "../AuthContext"
import { useToast } from "../ToastContext"

export default function Dashboard({ onViewReport }) {
  const { token, user } = useAuth()
  const toast = useToast()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  const fetchReports = () => {
    setLoading(true)
    fetch(`${API_URL}/api/reports`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => { setReports(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => { setLoading(false); toast.error("Failed to load", "Could not fetch reports.") })
  }

  useEffect(() => { fetchReports() }, [])

  const deleteReport = async (id, company, e) => {
    e.stopPropagation()
    if (!confirm(`Delete report for "${company}"?`)) return
    setDeleting(id)
    try {
      const r = await fetch(`${API_URL}/api/reports/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      })
      if (r.ok) {
        toast.success("Deleted", `Report for ${company} has been removed.`)
        fetchReports()
      }
    } catch {
      toast.error("Delete failed", "Please try again.")
    } finally {
      setDeleting(null)
    }
  }

  const stats = [
    { label: "Total Reports", value: reports.length, color: "var(--teal)", cls: "teal" },
    { label: "Generated Today", value: reports.filter(r => r.created_at?.startsWith(new Date().toISOString().slice(0,10))).length, color: "var(--gold)", cls: "gold" },
    { label: "Companies Tracked", value: [...new Set(reports.map(r => r.company))].length, color: "var(--green)", cls: "green" },
  ]

  const hour = new Date().getHours()
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"

  return (
    <div>
      {/* Header */}
      <div className="page-header animate-fade-up">
        <div className="page-eyebrow">Overview</div>
        <div className="page-title">{greeting}, {user?.username} 👋</div>
        <div className="page-sub">Here's what's happening across your intelligence pipeline.</div>
      </div>

      {/* Stats */}
      <div className="grid-3 animate-fade-up-1" style={{ marginBottom: 32 }}>
        {stats.map(({ label, value, color, cls }) => (
          <div key={label} className={`card stat-card ${cls}`}>
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={{ color }}>{value}</div>
            <div className="stat-trend">All time</div>
          </div>
        ))}
      </div>

      {/* Reports table */}
      <div className="card animate-fade-up-2">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 18, color: "var(--text)" }}>
              Recent Reports
            </div>
            <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 2 }}>
              Click any row to view full intelligence report
            </div>
          </div>
          <button className="btn btn-outline btn-sm" onClick={fetchReports}
            style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {loading ? <div className="spinner" /> : "↻"} Refresh
          </button>
        </div>

        {loading && reports.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
            <div className="spinner spinner-lg" />
          </div>
        ) : reports.length === 0 ? (
          <div className="empty-state">
            <div className="empty-illustration">◎</div>
            <div className="empty-title">No reports yet</div>
            <div className="empty-sub">
              Run Company Mode or Geography Mode to generate your first intelligence report.
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
              <button className="btn btn-primary btn-sm">Company Mode →</button>
              <button className="btn btn-outline btn-sm">Geography Mode</button>
            </div>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Generated</th>
                  <th>File</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id} onClick={() => onViewReport(r)}>
                    <td><span className="company-name">{r.company}</span></td>
                    <td><span className="mono-text">{new Date(r.created_at).toLocaleString()}</span></td>
                    <td><span className="mono-text">{r.filename}</span></td>
                    <td>
                      <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                        <button className="btn btn-outline btn-sm"
                          onClick={(e) => { e.stopPropagation(); onViewReport(r) }}>
                          View →
                        </button>
                        <button className="btn btn-danger btn-sm"
                          disabled={deleting === r.id}
                          onClick={(e) => deleteReport(r.id, r.company, e)}>
                          {deleting === r.id ? <div className="spinner" /> : "✕"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

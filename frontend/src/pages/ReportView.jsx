import { useState } from "react"
import { useAuth, API_URL } from "../AuthContext"
import { useToast } from "../ToastContext"

// ── Expandable section ──
function Section({ sectionKey, value }) {
  const [open, setOpen] = useState(true)
  const label = sectionKey.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()

  return (
    <div className="section-card">
      <div className="section-header" onClick={() => setOpen(o => !o)}>
        <span className="section-key">{label}</span>
        <span style={{ color: "var(--text3)", fontSize: 12, transition: "transform 0.2s", transform: open ? "rotate(180deg)" : "rotate(0)" }}>
          ▾
        </span>
      </div>
      {open && (
        <div className="section-body">
          <ValueRenderer value={value} />
        </div>
      )}
    </div>
  )
}

// ── Recursive value renderer ──
function ValueRenderer({ value, depth = 0 }) {
  if (value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) {
    return <span style={{ color: "var(--text3)", fontSize: 12, fontStyle: "italic" }}>Not available</span>
  }

  // Fact with source
  if (typeof value === "object" && !Array.isArray(value) && "value" in value && "source" in value) {
    return (
      <div>
        <div style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.6 }}>{value.value}</div>
        <a href={value.source} target="_blank" rel="noopener noreferrer" className="source-tag">
          ↗ {value.source}
        </a>
      </div>
    )
  }

  // Simple string
  if (typeof value === "string") {
    return <div style={{ fontSize: 14, color: "var(--text2)", lineHeight: 1.6 }}>{value}</div>
  }

  // Array
  if (Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {value.map((item, i) => (
          <div key={i} style={{
            padding: "12px 16px",
            background: "var(--bg3)",
            borderRadius: "var(--r-md)",
            border: "1px solid var(--border)",
            borderLeft: "3px solid var(--teal)",
          }}>
            {typeof item === "string" ? (
              <span style={{ fontSize: 13, color: "var(--text2)" }}>{item}</span>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {Object.entries(item).map(([k, v]) => {
                  const fieldLabel = k.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()
                  return (
                    <div key={k}>
                      <div style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: 9,
                        letterSpacing: "0.12em",
                        textTransform: "uppercase",
                        color: "var(--text3)",
                        marginBottom: 3
                      }}>
                        {fieldLabel}
                      </div>
                      {typeof v === "string" ? (
                        v.startsWith("http") ? (
                          <a href={v} target="_blank" rel="noopener noreferrer" className="source-tag">{v}</a>
                        ) : (
                          <div style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.5 }}>{v}</div>
                        )
                      ) : (
                        <ValueRenderer value={v} depth={depth + 1} />
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  // Object
  if (typeof value === "object") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {Object.entries(value).map(([k, v]) => {
          const fieldLabel = k.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()
          return (
            <div key={k}>
              <div style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: 9, letterSpacing: "0.12em",
                textTransform: "uppercase", color: "var(--text3)", marginBottom: 4
              }}>
                {fieldLabel}
              </div>
              <ValueRenderer value={v} depth={depth + 1} />
            </div>
          )
        })}
      </div>
    )
  }

  return <div style={{ fontSize: 13, color: "var(--text2)" }}>{String(value)}</div>
}

export default function ReportView({ report, onBack }) {
  const { token } = useAuth()
  const toast = useToast()
  const [tab, setTab] = useState("summary")
  const [exporting, setExporting] = useState(false)

  if (!report) return null

  const exportPDF = async () => {
    setExporting(true)
    try {
      const r = await fetch(`${API_URL}/api/reports/${report.id}/pdf`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!r.ok) {
        const err = await r.json()
        toast.error("Export failed", err.detail || "Could not generate PDF.")
        return
      }
      const blob = await r.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${report.company}_report.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success("PDF downloaded!", `${report.company} report saved.`)
    } catch {
      toast.error("Export failed", "Please try again.")
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="page-header animate-fade-up">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={onBack}>
            ← Back to Dashboard
          </button>
          <button className="btn btn-gold btn-sm" onClick={exportPDF} disabled={exporting}
            style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {exporting ? <><div className="spinner" style={{ borderTopColor: "var(--gold)" }} /> Generating...</> : "⬇ Export PDF"}
          </button>
        </div>
        <div className="page-eyebrow">Intelligence Report</div>
        <div className="page-title">{report.company}</div>
        <div className="page-sub">
          {new Date(report.created_at).toLocaleString()} · {report.filename}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, marginBottom: 24, borderBottom: "1px solid var(--border)" }}>
        {[["summary", "Summary"], ["json", "Raw JSON"]].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            padding: "10px 20px",
            background: "transparent", border: "none",
            borderBottom: tab === id ? "2px solid var(--teal)" : "2px solid transparent",
            color: tab === id ? "var(--teal)" : "var(--text3)",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 11, letterSpacing: "0.08em",
            textTransform: "uppercase", cursor: "pointer",
            marginBottom: -1, transition: "all 0.15s"
          }}>
            {label}
          </button>
        ))}
      </div>

      {tab === "summary" && (
        <div className="animate-fade-up">
          {!report.data || Object.keys(report.data).length === 0 ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-illustration">◎</div>
                <div className="empty-title">No data available</div>
                <div className="empty-sub">This report doesn't contain structured data.</div>
              </div>
            </div>
          ) : (
            Object.entries(report.data).map(([key, value]) => (
              <Section key={key} sectionKey={key} value={value} />
            ))
          )}
        </div>
      )}

      {tab === "json" && (
        <div className="card animate-fade-up">
          <div className="json-viewer">{JSON.stringify(report.data, null, 2)}</div>
        </div>
      )}
    </div>
  )
}

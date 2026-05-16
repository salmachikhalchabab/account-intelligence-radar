import { useState, useEffect, useRef } from "react"
import { useAuth, API_URL } from "../AuthContext"
import { useToast } from "../ToastContext"

const DEFAULT_OBJ = `Extract:
- Headquarters
- Business units and services
- Core products
- Official leadership (executives only)
- Top 5 recent strategic initiatives (AI, expansion, ERP, investments)

Return structured JSON with source for every fact.`

export default function CompanyMode() {
  const { token } = useAuth()
  const toast = useToast()
  const [company, setCompany] = useState("")
  const [useDefault, setUseDefault] = useState(true)
  const [objective, setObjective] = useState(DEFAULT_OBJ)
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const logRef = useRef(null)

  useEffect(() => {
    if (!jobId) return
    if (job?.status === "done" || job?.status === "error") return
    const interval = setInterval(async () => {
      try {
        const r = await fetch(`${API_URL}/api/job/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = await r.json()
        setJob(data)
        if (data.status === "done") {
          toast.success("Report ready!", `Intelligence report for ${company} is complete.`)
          clearInterval(interval)
        }
        if (data.status === "error") {
          toast.error("Job failed", data.error || "An error occurred.")
          clearInterval(interval)
        }
      } catch { clearInterval(interval) }
    }, 1500)
    return () => clearInterval(interval)
  }, [jobId, job?.status])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [job?.logs])

  const submit = async () => {
    if (!company.trim()) return
    setJob(null)
    try {
      const r = await fetch(`${API_URL}/api/company`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ company_name: company, objective: useDefault ? null : objective })
      })
      if (!r.ok) {
        const err = await r.json()
        toast.error("Invalid input", err.detail || "Please check your input.")
        return
      }
      const data = await r.json()
      setJobId(data.job_id)
      setJob({ status: "pending", logs: [] })
      toast.info("Job started", `Researching ${company}...`)
    } catch {
      toast.error("Network error", "Could not connect to the API.")
    }
  }

  const isRunning = job?.status === "running" || job?.status === "pending"

  return (
    <div>
      <div className="page-header animate-fade-up">
        <div className="page-eyebrow">Intelligence Pipeline</div>
        <div className="page-title">Company Mode</div>
        <div className="page-sub">Generate a structured intelligence report for any company.</div>
      </div>

      <div className="grid-2" style={{ gap: 28, alignItems: "start" }}>
        {/* Form */}
        <div className="card animate-fade-up-1">
          <div className="form-group">
            <label className="form-label">Company Name</label>
            <div style={{ position: "relative" }}>
              <span style={{
                position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)",
                color: "var(--text3)", fontSize: 14, pointerEvents: "none"
              }}>◎</span>
              <input
                className="form-input"
                placeholder="e.g. Aramco, STC, SABIC..."
                value={company}
                onChange={e => setCompany(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !isRunning && submit()}
                style={{ paddingLeft: 40 }}
              />
            </div>
          </div>

          <div className="toggle-row">
            <label className="toggle">
              <input type="checkbox" checked={useDefault} onChange={e => setUseDefault(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
            <span style={{ fontSize: 13, color: "var(--text2)" }}>Use default objective</span>
          </div>

          {useDefault ? (
            <div style={{
              background: "var(--bg)",
              border: "1px solid var(--border)",
              borderRadius: "var(--r-md)",
              padding: "14px 16px",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: 11.5,
              color: "var(--text3)",
              lineHeight: 1.9,
              marginBottom: 20,
              whiteSpace: "pre-wrap"
            }}>
              {DEFAULT_OBJ}
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Custom Objective</label>
              <textarea className="form-textarea" value={objective}
                onChange={e => setObjective(e.target.value)} />
            </div>
          )}

          <button className="btn btn-primary"
            onClick={submit}
            disabled={isRunning || !company.trim()}
            style={{ width: "100%", padding: "13px", fontSize: 15 }}>
            {isRunning ? (
              <><div className="spinner" /> Researching...</>
            ) : "Run Intelligence ◎"}
          </button>
        </div>

        {/* Results */}
        <div>
          {!job && (
            <div className="card animate-fade-up-2" style={{ textAlign: "center", padding: "48px 24px" }}>
              <div style={{ fontSize: 40, marginBottom: 16, color: "var(--text4)" }}>◎</div>
              <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 18, color: "var(--text3)", marginBottom: 8 }}>
                Ready to research
              </div>
              <div style={{ fontSize: 13, color: "var(--text3)" }}>
                Enter a company name and run intelligence to see results here.
              </div>
            </div>
          )}

          {job && (
            <div className="card animate-fade-up" style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 17 }}>Job Status</div>
                <span className={`badge badge-${job.status}`}>
                  {job.status === "running" && <div className="pulse" />}
                  {job.status}
                </span>
              </div>
              {job.logs?.length > 0 && (
                <div className="log-box" ref={logRef}>
                  {job.logs.map((l, i) => <div key={i} className="log-line">{l}</div>)}
                </div>
              )}
            </div>
          )}

          {job?.status === "done" && job?.result && (
            <div className="card animate-fade-up">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 17 }}>Result</div>
                <span className="badge badge-done">✓ Complete</span>
              </div>
              <div className="json-viewer">{JSON.stringify(job.result, null, 2)}</div>
              {job.paths && (
                <div style={{
                  marginTop: 12, padding: "10px 14px",
                  background: "var(--bg)", borderRadius: "var(--r-md)",
                  fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "var(--text3)"
                }}>
                  <div>📄 {job.paths.json}</div>
                  <div style={{ marginTop: 4 }}>📝 {job.paths.markdown}</div>
                </div>
              )}
            </div>
          )}

          {job?.status === "error" && (
            <div className="card animate-fade-up" style={{ borderColor: "rgba(239,68,68,0.25)" }}>
              <div className="badge badge-error" style={{ marginBottom: 12 }}>✕ Error</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--red)", lineHeight: 1.6 }}>
                {job.error}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

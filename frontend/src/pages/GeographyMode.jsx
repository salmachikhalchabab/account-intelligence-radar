import { useState, useEffect, useRef } from "react"
import { useAuth, API_URL } from "../AuthContext"
import { useToast } from "../ToastContext"

export default function GeographyMode() {
  const { token } = useAuth()
  const toast = useToast()
  const [form, setForm] = useState({ country: "", city: "", sector: "" })
  const [useDefault, setUseDefault] = useState(true)
  const [objective, setObjective] = useState("")
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const logRef = useRef(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

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
          toast.success("Research complete!", `All companies processed.`)
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
    if (!form.country.trim() || !form.sector.trim()) return
    setJob(null)
    try {
      const r = await fetch(`${API_URL}/api/geography`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ country: form.country, city: form.city, sector: form.sector, objective: useDefault ? null : objective })
      })
      if (!r.ok) {
        const err = await r.json()
        toast.error("Invalid input", err.detail || "Please check your input.")
        return
      }
      const data = await r.json()
      setJobId(data.job_id)
      setJob({ status: "pending", logs: [] })
      toast.info("Job started", `Discovering companies in ${form.country}...`)
    } catch {
      toast.error("Network error", "Could not connect to the API.")
    }
  }

  const isRunning = job?.status === "running" || job?.status === "pending"

  return (
    <div>
      <div className="page-header animate-fade-up">
        <div className="page-eyebrow">Intelligence Pipeline</div>
        <div className="page-title">Geography Mode</div>
        <div className="page-sub">Discover and research top companies in any region and sector.</div>
      </div>

      <div className="grid-2" style={{ gap: 28, alignItems: "start" }}>
        {/* Form */}
        <div className="card animate-fade-up-1">
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Country *</label>
              <input className="form-input no-icon" placeholder="e.g. Saudi Arabia"
                value={form.country} onChange={e => set("country", e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">City <span style={{ color: "var(--text3)" }}>(optional)</span></label>
              <input className="form-input no-icon" placeholder="e.g. Riyadh"
                value={form.city} onChange={e => set("city", e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Target Sector *</label>
            <input className="form-input no-icon"
              placeholder="e.g. energy, fintech, manufacturing..."
              value={form.sector} onChange={e => set("sector", e.target.value)} />
          </div>

          {/* Warning */}
          <div style={{
            background: "rgba(212,168,71,0.05)",
            border: "1px solid rgba(212,168,71,0.18)",
            borderRadius: "var(--r-md)",
            padding: "12px 16px",
            marginBottom: 20,
            display: "flex", gap: 10, alignItems: "flex-start"
          }}>
            <span style={{ color: "var(--gold)", fontSize: 14, marginTop: 1 }}>⚠</span>
            <div style={{ fontSize: 12, color: "var(--gold)", lineHeight: 1.6 }}>
              Geography Mode runs up to <strong>3 companies</strong> — consumes SerpAPI + LLM + Firecrawl credits.
            </div>
          </div>

          <div className="toggle-row">
            <label className="toggle">
              <input type="checkbox" checked={useDefault} onChange={e => setUseDefault(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
            <span style={{ fontSize: 13, color: "var(--text2)" }}>Use default objective</span>
          </div>

          {!useDefault && (
            <div className="form-group">
              <label className="form-label">Custom Objective</label>
              <textarea className="form-textarea" value={objective}
                onChange={e => setObjective(e.target.value)}
                placeholder="What intelligence do you need?" />
            </div>
          )}

          <button className="btn btn-primary"
            onClick={submit}
            disabled={isRunning || !form.country.trim() || !form.sector.trim()}
            style={{ width: "100%", padding: "13px", fontSize: 15 }}>
            {isRunning ? (
              <><div className="spinner" /> Researching...</>
            ) : "Discover Companies ◈"}
          </button>
        </div>

        {/* Results */}
        <div>
          {!job && (
            <div className="card animate-fade-up-2" style={{ textAlign: "center", padding: "48px 24px" }}>
              <div style={{ fontSize: 40, marginBottom: 16, color: "var(--text4)" }}>◈</div>
              <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 18, color: "var(--text3)", marginBottom: 8 }}>
                Awaiting your query
              </div>
              <div style={{ fontSize: 13, color: "var(--text3)" }}>
                Enter a country and sector to discover and research top companies.
              </div>
            </div>
          )}

          {job && (
            <div className="card animate-fade-up" style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 17 }}>Status</div>
                <span className={`badge badge-${job.status}`}>
                  {(job.status === "running" || job.status === "pending") && <div className="pulse" />}
                  {job.status}
                </span>
              </div>

              {job.companies?.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", color: "var(--text3)", marginBottom: 8 }}>
                    Shortlisted Companies
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {job.companies.map((c, i) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", gap: 12,
                        padding: "10px 14px",
                        background: "var(--bg3)",
                        borderRadius: "var(--r-md)",
                        border: "1px solid var(--border)"
                      }}>
                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "var(--teal)", minWidth: 20 }}>
                          0{i + 1}
                        </span>
                        <span style={{ fontFamily: "Instrument Serif, serif", fontSize: 15 }}>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {job.logs?.length > 0 && (
                <div className="log-box" ref={logRef}>
                  {job.logs.map((l, i) => <div key={i} className="log-line">{l}</div>)}
                </div>
              )}
            </div>
          )}

          {job?.status === "done" && job?.company_results && (
            <div className="card animate-fade-up">
              <div style={{ fontFamily: "Instrument Serif, serif", fontSize: 17, marginBottom: 16 }}>Results</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {job.company_results.map((cr, i) => (
                  <div key={i} style={{
                    padding: "14px 16px",
                    background: "var(--bg3)",
                    borderRadius: "var(--r-md)",
                    border: "1px solid var(--border)"
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: cr.result ? 12 : 0 }}>
                      <span style={{ fontFamily: "Instrument Serif, serif", fontSize: 15 }}>{cr.company}</span>
                      <span className={`badge badge-${cr.status}`}>{cr.status}</span>
                    </div>
                    {cr.result && (
                      <div className="json-viewer" style={{ maxHeight: 180, fontSize: 11 }}>
                        {JSON.stringify(cr.result, null, 2)}
                      </div>
                    )}
                    {cr.error && (
  <div style={{ fontSize: 12, color: "var(--amber)", marginTop: 6, lineHeight: 1.6 }}>
    ⚠ Could not verify this company in {form.country}.
    It may operate under a different name locally or have limited online presence.
  </div>
)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {job?.status === "error" && (
            <div className="card animate-fade-up" style={{ borderColor: "rgba(239,68,68,0.25)" }}>
              <div className="badge badge-error" style={{ marginBottom: 12 }}>✕ Error</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--red)" }}>
                {job.error}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

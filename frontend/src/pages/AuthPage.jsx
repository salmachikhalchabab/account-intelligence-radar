import { useState, useEffect } from "react"
import { useAuth } from "../AuthContext"
import { useToast } from "../ToastContext"

// ── Real-time validation ──
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function getPasswordStrength(password) {
  if (!password) return { score: 0, label: "", level: "" }
  let score = 0
  if (password.length >= 8)           score++
  if (/[A-Z]/.test(password))         score++
  if (/[0-9]/.test(password))         score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  const levels = ["", "weak", "fair", "good", "strong"]
  const labels = ["", "Weak", "Fair", "Good", "Strong"]
  return { score, label: labels[score], level: levels[score] }
}

// ── Password strength bar ──
function PasswordStrength({ password }) {
  const { score, label, level } = getPasswordStrength(password)
  if (!password) return null

  return (
    <div style={{ marginTop: 8 }}>
      <div className="password-strength">
        {[1, 2, 3, 4].map(i => (
          <div key={i}
            className={`strength-bar ${i <= score ? `active ${level}` : ""}`}
          />
        ))}
      </div>
      <div className="strength-label"
        style={{ color: score <= 1 ? "var(--red)" : score === 2 ? "var(--amber)" : score === 3 ? "var(--teal)" : "var(--green)" }}>
        {label}
      </div>
    </div>
  )
}

// ── Validation checklist ──
function ValidationList({ password }) {
  if (!password) return null
  const checks = [
    { label: "At least 8 characters", pass: password.length >= 8 },
    { label: "One uppercase letter",  pass: /[A-Z]/.test(password) },
    { label: "One number",            pass: /[0-9]/.test(password) },
  ]
  return (
    <div className="validation-list">
      {checks.map(({ label, pass }) => (
        <div key={label} className={`validation-item ${pass ? "pass" : ""}`}>
          <span className="check">{pass ? "✓" : "○"}</span>
          <span>{label}</span>
        </div>
      ))}
    </div>
  )
}

export default function AuthPage() {
  const [mode, setMode] = useState("login")
  const [form, setForm] = useState({ email: "", username: "", password: "" })
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const toast = useToast()

  const set = (k, v) => {
    setForm(f => ({ ...f, [k]: v }))
    // Clear error on change
    if (errors[k]) setErrors(e => ({ ...e, [k]: "" }))
  }

  const touch = (k) => setTouched(t => ({ ...t, [k]: true }))

  // Real-time validation
  const validate = () => {
    const errs = {}
    if (mode === "register") {
      if (!form.email) errs.email = "Email is required"
      else if (!validateEmail(form.email)) errs.email = "Enter a valid email address"

      if (!form.username) errs.username = "Username is required"
      else if (form.username.length < 3) errs.username = "Username must be at least 3 characters"

      const { score } = getPasswordStrength(form.password)
      if (!form.password) errs.password = "Password is required"
      else if (form.password.length < 8) errs.password = "Password must be at least 8 characters"
      else if (!/[A-Z]/.test(form.password)) errs.password = "Add at least one uppercase letter"
      else if (!/[0-9]/.test(form.password)) errs.password = "Add at least one number"
    } else {
      if (!form.username) errs.username = "Email or username is required"
      if (!form.password) errs.password = "Password is required"
    }
    return errs
  }

  const submit = async () => {
    const allTouched = { email: true, username: true, password: true }
    setTouched(allTouched)
    const errs = validate()
    setErrors(errs)
    if (Object.keys(errs).length > 0) return

    setLoading(true)
    try {
      if (mode === "login") {
        await login(form.username, form.password)
        toast.success("Welcome back!", "You have been signed in successfully.")
      } else {
        await register(form.email, form.username, form.password)
        toast.success("Account created!", "Welcome to Intelligence Radar.")
      }
    } catch (e) {
      const msg = e.message || ""
      // Map backend errors to friendly messages
      if (msg.includes("Email already") || msg.includes("already registered")) {
        setErrors(prev => ({ ...prev, email: "This email is already registered" }))
      } else if (msg.includes("Username already") || msg.includes("already taken")) {
        setErrors(prev => ({ ...prev, username: "This username is already taken" }))
      } else if (msg.includes("Incorrect") || msg.includes("401")) {
        setErrors(prev => ({ ...prev, password: "Invalid email or password" }))
      } else if (msg.includes("disabled")) {
        setErrors(prev => ({ ...prev, username: "This account has been disabled" }))
      } else {
        toast.error("Something went wrong", msg || "Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (m) => {
    setMode(m)
    setErrors({})
    setTouched({})
    setForm({ email: "", username: "", password: "" })
  }

  const inputClass = (field) => {
    const base = "form-input"
    if (touched[field] && errors[field]) return base + " error"
    if (touched[field] && !errors[field] && form[field]) return base + " success"
    return base
  }

  return (
    <div className="auth-bg">
      <div className="auth-orb-1" />
      <div className="auth-orb-2" />

      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-mark">◈</div>
          <span className="auth-logo-name">Intelligence Radar</span>
          <span className="auth-logo-sub">by Averroa</span>
        </div>

        <div className="auth-panel">
          {/* Tabs */}
          <div className="auth-tabs">
            {["login", "register"].map(m => (
              <button key={m}
                className={`auth-tab ${mode === m ? "active" : ""}`}
                onClick={() => switchMode(m)}>
                {m === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>

          {/* Register: Email */}
          {mode === "register" && (
            <div className="form-group animate-fade-up">
              <label className="form-label">Email Address</label>
              <div className="input-wrapper">
                <span className="input-icon">@</span>
                <input
                  className={inputClass("email")}
                  type="email"
                  placeholder="you@company.com"
                  value={form.email}
                  onChange={e => set("email", e.target.value)}
                  onBlur={() => touch("email")}
                />
              </div>
              {touched.email && errors.email && (
                <div className="form-error">⚠ {errors.email}</div>
              )}
            </div>
          )}

          {/* Username / Email or Username */}
          <div className="form-group animate-fade-up-1">
            <label className="form-label">
              {mode === "login" ? "Email or Username" : "Username"}
            </label>
            <div className="input-wrapper">
              <span className="input-icon">◎</span>
              <input
                className={inputClass("username")}
                placeholder={mode === "login" ? "Enter email or username" : "Choose a username"}
                value={form.username}
                onChange={e => set("username", e.target.value)}
                onBlur={() => touch("username")}
                onKeyDown={e => e.key === "Enter" && submit()}
              />
            </div>
            {touched.username && errors.username && (
              <div className="form-error">⚠ {errors.username}</div>
            )}
          </div>

          {/* Password */}
          <div className="form-group animate-fade-up-2">
            <label className="form-label">Password</label>
            <div className="input-wrapper">
              <span className="input-icon">◆</span>
              <input
                className={inputClass("password")}
                type={showPassword ? "text" : "password"}
                placeholder={mode === "register" ? "Create a strong password" : "Enter your password"}
                value={form.password}
                onChange={e => set("password", e.target.value)}
                onBlur={() => touch("password")}
                onKeyDown={e => e.key === "Enter" && submit()}
                style={{ paddingRight: 40 }}
              />
              <button className="password-toggle" onClick={() => setShowPassword(s => !s)}>
                {showPassword ? "◡" : "◉"}
              </button>
            </div>
            {touched.password && errors.password && (
              <div className="form-error">⚠ {errors.password}</div>
            )}
            {mode === "register" && (
              <>
                <PasswordStrength password={form.password} />
                <ValidationList password={form.password} />
              </>
            )}
          </div>

          {/* Submit */}
          <button
            className="btn btn-primary animate-fade-up-3"
            onClick={submit}
            disabled={loading}
            style={{ width: "100%", padding: "13px", fontSize: 15, marginTop: 4 }}
          >
            {loading ? (
              <><div className="spinner" /> {mode === "login" ? "Signing in..." : "Creating account..."}</>
            ) : (
              mode === "login" ? "Sign In →" : "Create Account →"
            )}
          </button>
        </div>

        <div className="auth-footer">
          Your data is stored locally and never shared with third parties.
        </div>
      </div>
    </div>
  )
}

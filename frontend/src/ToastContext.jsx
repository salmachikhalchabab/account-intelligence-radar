import { createContext, useContext, useState, useCallback } from "react"

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts(t => t.map(toast =>
      toast.id === id ? { ...toast, exiting: true } : toast
    ))
    setTimeout(() => setToasts(t => t.filter(toast => toast.id !== id)), 280)
  }, [])

  const show = useCallback(({ type = "info", title, message, duration = 4000 }) => {
    const id = Date.now() + Math.random()
    setToasts(t => [...t, { id, type, title, message }])
    if (duration > 0) setTimeout(() => dismiss(id), duration)
    return id
  }, [dismiss])

  const success = useCallback((title, message) => show({ type: "success", title, message }), [show])
  const error   = useCallback((title, message) => show({ type: "error",   title, message }), [show])
  const info    = useCallback((title, message) => show({ type: "info",    title, message }), [show])

  const icons = { success: "✓", error: "✕", info: "◎" }
  const colors = {
    success: "var(--green)",
    error:   "var(--red)",
    info:    "var(--teal)",
  }

  return (
    <ToastContext.Provider value={{ show, success, error, info }}>
      {children}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id}
            className={`toast toast-${toast.type} ${toast.exiting ? "exiting" : ""}`}>
            <div className="toast-icon" style={{ color: colors[toast.type] }}>
              {icons[toast.type]}
            </div>
            <div className="toast-body">
              {toast.title && <div className="toast-title">{toast.title}</div>}
              {toast.message && <div className="toast-msg">{toast.message}</div>}
            </div>
            <button onClick={() => dismiss(toast.id)} style={{
              background: "none", border: "none", color: "var(--text3)",
              cursor: "pointer", fontSize: 16, padding: "2px 4px",
              lineHeight: 1, alignSelf: "flex-start"
            }}>×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)

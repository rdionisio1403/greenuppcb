import React, { useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";

export default function ConfirmModal({
  open,
  title = "Are you sure?",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  loading = false,
  danger = true,
}) {
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !loading) {
        onCancel();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, loading, onCancel]);

  if (!open) return null;

  return (
    <div
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !loading) {
          onCancel();
        }
      }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        background: "rgba(2, 6, 23, 0.62)",
        backdropFilter: "blur(4px)",
      }}
    >
      <section
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        aria-describedby="confirm-modal-message"
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "26px",
          border: "1px solid var(--app-border)",
          borderRadius: "18px",
          background: "var(--app-surface)",
          color: "var(--app-text)",
          boxShadow: "0 24px 70px rgba(0, 0, 0, 0.28)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "16px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "46px",
              height: "46px",
              flexShrink: 0,
              borderRadius: "14px",
              background: danger
                ? "var(--app-error-bg)"
                : "var(--app-surface-muted)",
              color: danger
                ? "var(--app-error-text)"
                : "var(--app-text)",
            }}
          >
            <AlertTriangle size={23} />
          </div>

          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            aria-label="Close dialog"
            style={{
              display: "flex",
              padding: "6px",
              border: "none",
              borderRadius: "8px",
              background: "transparent",
              color: "var(--app-text-muted)",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            <X size={20} />
          </button>
        </div>

        <h2
          id="confirm-modal-title"
          style={{
            margin: "18px 0 8px",
            fontSize: "1.2rem",
            fontWeight: 700,
            lineHeight: 1.4,
          }}
        >
          {title}
        </h2>

        <p
          id="confirm-modal-message"
          style={{
            margin: 0,
            color: "var(--app-text-muted)",
            fontSize: "0.95rem",
            lineHeight: 1.65,
            overflowWrap: "anywhere",
          }}
        >
          {message}
        </p>

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            flexWrap: "wrap",
            gap: "10px",
            marginTop: "26px",
          }}
        >
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: "10px 16px",
              border: "1px solid var(--app-border)",
              borderRadius: "9px",
              background: "var(--app-surface)",
              color: "var(--app-text)",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {cancelText}
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: "10px 16px",
              border: `1px solid ${
                danger ? "var(--app-error-border)" : "var(--app-border)"
              }`,
              borderRadius: "9px",
              background: danger
                ? "var(--app-error-text)"
                : "var(--app-text)",
              color: danger
                ? "var(--app-surface)"
                : "var(--app-surface)",
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Please wait..." : confirmText}
          </button>
        </div>
      </section>
    </div>
  );
}

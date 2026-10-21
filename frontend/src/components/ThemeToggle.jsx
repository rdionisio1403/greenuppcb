import { useEffect, useState } from "react";

function getInitialTheme() {
  try {
    const savedTheme = localStorage.getItem("greenupcb-theme");
    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }
  } catch {
    // Fall back to the operating system preference.
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);

    try {
      localStorage.setItem("greenupcb-theme", theme);
    } catch {
      // Theme still works for the current page if storage is unavailable.
    }
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", nextTheme);

    try {
      localStorage.setItem("greenupcb-theme", nextTheme);
    } catch {
      // Keep the current-page toggle working.
    }

    setTheme(nextTheme);
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={theme === "dark"}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      style={{
        position: "fixed",
        top: "20px",
        right: "20px",
        zIndex: 1000,
        padding: "8px 12px",
        border: "1px solid var(--app-border)",
        borderRadius: "8px",
        background: "var(--app-surface)",
        color: "var(--app-text)",
        fontWeight: 600,
        cursor: "pointer",
      }}
    >
      {theme === "dark" ? "☀️ Light mode" : "🌙 Dark mode"}
    </button>
  );
}

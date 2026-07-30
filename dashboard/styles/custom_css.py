"""
EcoPredict AI — premium 2026 theme system.

Deep navy / teal / emerald palette, glassmorphism cards, refined typography.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

# Google fonts + CSS variables (injected once per theme)
_FONT_LINK = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400"
    "&family=JetBrains+Mono:wght@400;500;600"
    "&display=swap"
)

_STYLES_DIR = Path(__file__).resolve().parent

DARK_CSS = r"""
:root {
  --ep-bg-0: #070b14;
  --ep-bg-1: #0c1222;
  --ep-bg-2: #121a2e;
  --ep-surface: rgba(18, 28, 48, 0.72);
  --ep-surface-2: rgba(24, 36, 58, 0.88);
  --ep-border: rgba(148, 180, 220, 0.12);
  --ep-border-strong: rgba(56, 189, 248, 0.28);
  --ep-text: #e8eef8;
  --ep-text-muted: #8b9bb8;
  --ep-accent: #38bdf8;
  --ep-accent-2: #2dd4bf;
  --ep-accent-3: #a78bfa;
  --ep-success: #34d399;
  --ep-warn: #fbbf24;
  --ep-danger: #f87171;
  --ep-solar: #fbbf24;
  --ep-wind: #38bdf8;
  --ep-grid: #a78bfa;
  --ep-radius: 18px;
  --ep-radius-sm: 12px;
  --ep-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  --ep-glow: 0 0 40px rgba(56, 189, 248, 0.12);
  --ep-font: 'DM Sans', 'Segoe UI', system-ui, sans-serif;
  --ep-mono: 'JetBrains Mono', ui-monospace, monospace;
}

html, body, [class*="css"] {
  font-family: var(--ep-font) !important;
}

h1, h2, h3, h4, h5 {
  font-family: var(--ep-font) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  color: var(--ep-text) !important;
}

/* App shell */
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(56, 189, 248, 0.14), transparent 55%),
    radial-gradient(900px 500px at 90% 0%, rgba(45, 212, 191, 0.10), transparent 50%),
    radial-gradient(800px 400px at 50% 100%, rgba(167, 139, 250, 0.08), transparent 55%),
    linear-gradient(165deg, var(--ep-bg-0) 0%, var(--ep-bg-1) 45%, var(--ep-bg-2) 100%) !important;
  color: var(--ep-text) !important;
}

[data-testid="stHeader"] {
  background: rgba(7, 11, 20, 0.55) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  border-bottom: 1px solid var(--ep-border) !important;
}

.main .block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 3rem !important;
  max-width: 1280px !important;
}

/* Sidebar glass */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(10, 16, 30, 0.98) 0%, rgba(12, 18, 34, 0.96) 100%) !important;
  border-right: 1px solid var(--ep-border) !important;
}
[data-testid="stSidebar"] > div:first-child {
  background: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
  color: var(--ep-text-muted) !important;
}

/* Tabs — pill navigation */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.4rem !important;
  background: rgba(12, 18, 34, 0.55) !important;
  padding: 0.45rem !important;
  border-radius: 14px !important;
  border: 1px solid var(--ep-border) !important;
  overflow-x: auto !important;
  flex-wrap: nowrap !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  padding: 0.55rem 1rem !important;
  color: var(--ep-text-muted) !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  background: transparent !important;
  border: none !important;
  white-space: nowrap !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.22), rgba(45, 212, 191, 0.16)) !important;
  color: var(--ep-text) !important;
  box-shadow: inset 0 0 0 1px var(--ep-border-strong) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  display: none !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding-top: 1.25rem !important;
}

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, #0ea5e9 0%, #14b8a6 100%) !important;
  color: #041018 !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.65rem 1.35rem !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 8px 24px rgba(14, 165, 233, 0.28) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 28px rgba(45, 212, 191, 0.35) !important;
}
.stButton > button[kind="secondary"] {
  background: rgba(24, 36, 58, 0.9) !important;
  color: var(--ep-text) !important;
  box-shadow: none !important;
  border: 1px solid var(--ep-border) !important;
}

/* Inputs */
.stSelectbox > div > div,
.stNumberInput > div > div,
.stTextInput > div > div,
.stTextArea > div > div {
  background: rgba(12, 18, 34, 0.75) !important;
  border-radius: 12px !important;
  border-color: var(--ep-border) !important;
  color: var(--ep-text) !important;
}

/* Metrics (native) */
[data-testid="stMetric"] {
  background: var(--ep-surface) !important;
  border: 1px solid var(--ep-border) !important;
  border-radius: var(--ep-radius-sm) !important;
  padding: 0.85rem 1rem !important;
  box-shadow: var(--ep-shadow) !important;
  backdrop-filter: blur(12px) !important;
}
[data-testid="stMetricLabel"] { color: var(--ep-text-muted) !important; }
[data-testid="stMetricValue"] {
  color: var(--ep-text) !important;
  font-weight: 700 !important;
}

/* Expanders / containers */
[data-testid="stExpander"] {
  background: var(--ep-surface) !important;
  border: 1px solid var(--ep-border) !important;
  border-radius: var(--ep-radius-sm) !important;
}

/* Alerts */
.stAlert {
  border-radius: var(--ep-radius-sm) !important;
  border: 1px solid var(--ep-border) !important;
  backdrop-filter: blur(8px) !important;
}

/* Dividers */
hr {
  border-color: var(--ep-border) !important;
  opacity: 0.7 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
  border-radius: var(--ep-radius-sm) !important;
  overflow: hidden !important;
  border: 1px solid var(--ep-border) !important;
}

/* Plotly */
.js-plotly-plot .plotly {
  border-radius: var(--ep-radius-sm) !important;
}

/* —— Component classes —— */
.ep-hero {
  position: relative;
  border-radius: 22px;
  padding: 1.75rem 1.9rem 1.5rem;
  margin-bottom: 1.25rem;
  background:
    linear-gradient(135deg, rgba(14, 165, 233, 0.16) 0%, rgba(45, 212, 191, 0.08) 45%, rgba(167, 139, 250, 0.10) 100%),
    var(--ep-surface);
  border: 1px solid var(--ep-border);
  box-shadow: var(--ep-shadow), var(--ep-glow);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  overflow: hidden;
}
.ep-hero::before {
  content: "";
  position: absolute;
  inset: -40% auto auto 55%;
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.22), transparent 70%);
  pointer-events: none;
}
.ep-hero-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ep-accent-2);
  margin-bottom: 0.55rem;
}
.ep-hero h1 {
  margin: 0 0 0.45rem 0 !important;
  font-size: clamp(1.55rem, 2.6vw, 2.05rem) !important;
  background: linear-gradient(105deg, #f0f9ff 0%, #7dd3fc 45%, #5eead4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2 !important;
}
.ep-hero-sub {
  color: var(--ep-text-muted);
  font-size: 1rem;
  line-height: 1.55;
  max-width: 52rem;
  margin: 0;
}
.ep-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.1rem;
}

.ep-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  border: 1px solid var(--ep-border);
  background: rgba(8, 14, 26, 0.45);
  color: var(--ep-text-muted);
}
.ep-pill--ok {
  color: #6ee7b7;
  border-color: rgba(52, 211, 153, 0.35);
  background: rgba(16, 185, 129, 0.12);
}
.ep-pill--warn {
  color: #fcd34d;
  border-color: rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.10);
}
.ep-pill--err {
  color: #fca5a5;
  border-color: rgba(248, 113, 113, 0.35);
  background: rgba(248, 113, 113, 0.10);
}
.ep-pill--accent {
  color: #7dd3fc;
  border-color: rgba(56, 189, 248, 0.35);
  background: rgba(14, 165, 233, 0.12);
}

.ep-card {
  background: var(--ep-surface);
  border: 1px solid var(--ep-border);
  border-radius: var(--ep-radius);
  padding: 1.15rem 1.25rem;
  box-shadow: var(--ep-shadow);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
  height: 100%;
}
.ep-card:hover {
  border-color: var(--ep-border-strong);
  transform: translateY(-3px);
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.4), var(--ep-glow);
}
.ep-card-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ep-text-muted);
  margin-bottom: 0.45rem;
}
.ep-card-value {
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}
.ep-card-value--solar {
  background: linear-gradient(90deg, #fcd34d, #f59e0b);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.ep-card-value--wind {
  background: linear-gradient(90deg, #7dd3fc, #0ea5e9);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.ep-card-value--total {
  background: linear-gradient(90deg, #6ee7b7, #2dd4bf);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.ep-card-value--default {
  background: linear-gradient(90deg, #e0e7ff, #a5b4fc);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.ep-card-hint {
  margin-top: 0.4rem;
  font-size: 0.82rem;
  color: var(--ep-text-muted);
}

.ep-section-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--ep-text);
  margin: 0.25rem 0 0.85rem 0;
}
.ep-section-title span.ep-bar {
  width: 4px;
  height: 1.15rem;
  border-radius: 4px;
  background: linear-gradient(180deg, var(--ep-accent), var(--ep-accent-2));
  display: inline-block;
}

.ep-module-tile {
  background: var(--ep-surface-2);
  border: 1px solid var(--ep-border);
  border-radius: 16px;
  padding: 1.1rem 1.15rem;
  height: 100%;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.ep-module-tile:hover {
  border-color: var(--ep-border-strong);
  transform: translateY(-2px);
}
.ep-module-tile h4 {
  margin: 0.35rem 0 0.35rem 0 !important;
  font-size: 1rem !important;
  color: var(--ep-text) !important;
}
.ep-module-tile p {
  margin: 0;
  font-size: 0.86rem;
  color: var(--ep-text-muted);
  line-height: 1.45;
}
.ep-module-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(45, 212, 191, 0.12));
  border: 1px solid var(--ep-border);
  font-size: 1.1rem;
}

.ep-footer {
  margin-top: 2.5rem;
  padding: 1.25rem 0 0.5rem;
  border-top: 1px solid var(--ep-border);
  text-align: center;
  color: var(--ep-text-muted);
  font-size: 0.82rem;
  line-height: 1.6;
}
.ep-footer strong {
  color: var(--ep-text);
  font-weight: 600;
}
.ep-footer a { color: var(--ep-accent); text-decoration: none; }

/* Brand block in sidebar */
.ep-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.35rem 0.15rem 0.85rem;
  border-bottom: 1px solid var(--ep-border);
  margin-bottom: 0.85rem;
}
.ep-brand-mark {
  width: 42px; height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  background: linear-gradient(145deg, #0ea5e9, #14b8a6);
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.35);
  color: #041018;
  font-weight: 800;
}
.ep-brand-text strong {
  display: block;
  color: var(--ep-text);
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}
.ep-brand-text span {
  display: block;
  color: var(--ep-text-muted);
  font-size: 0.75rem;
  margin-top: 0.1rem;
}

/* Legacy energy-card compat */
.energy-card {
  background: var(--ep-surface) !important;
  border: 1px solid var(--ep-border) !important;
  border-radius: var(--ep-radius) !important;
  padding: 1.15rem !important;
  margin-bottom: 0.75rem !important;
  box-shadow: var(--ep-shadow) !important;
  backdrop-filter: blur(12px) !important;
}
.metric-value {
  font-size: 1.85rem;
  font-weight: 700;
  margin-top: 0.25rem;
}

/* Icon helpers */
.ep-icon { display: inline-block; vertical-align: -0.2em; }
.ep-icon-label { display: inline-flex; align-items: center; gap: 0.35rem; }
"""

LIGHT_CSS = r"""
:root {
  --ep-bg-0: #f4f7fb;
  --ep-bg-1: #eef2f8;
  --ep-bg-2: #e8eef7;
  --ep-surface: rgba(255, 255, 255, 0.82);
  --ep-surface-2: rgba(255, 255, 255, 0.92);
  --ep-border: rgba(15, 23, 42, 0.08);
  --ep-border-strong: rgba(14, 165, 233, 0.35);
  --ep-text: #0f172a;
  --ep-text-muted: #64748b;
  --ep-accent: #0284c7;
  --ep-accent-2: #0d9488;
  --ep-accent-3: #7c3aed;
  --ep-success: #059669;
  --ep-warn: #d97706;
  --ep-danger: #dc2626;
  --ep-radius: 18px;
  --ep-radius-sm: 12px;
  --ep-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
  --ep-glow: 0 0 30px rgba(14, 165, 233, 0.08);
  --ep-font: 'DM Sans', 'Segoe UI', system-ui, sans-serif;
  --ep-mono: 'JetBrains Mono', ui-monospace, monospace;
}

html, body, [class*="css"] { font-family: var(--ep-font) !important; }
h1, h2, h3, h4 { font-family: var(--ep-font) !important; font-weight: 700 !important; color: var(--ep-text) !important; }

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1000px 500px at 0% 0%, rgba(14, 165, 233, 0.10), transparent 50%),
    radial-gradient(800px 400px at 100% 0%, rgba(13, 148, 136, 0.08), transparent 50%),
    linear-gradient(165deg, #f8fafc 0%, #eef2ff 55%, #f0fdfa 100%) !important;
  color: var(--ep-text) !important;
}
[data-testid="stHeader"] {
  background: rgba(255,255,255,0.7) !important;
  backdrop-filter: blur(12px) !important;
  border-bottom: 1px solid var(--ep-border) !important;
}
.main .block-container { padding-top: 1.25rem !important; max-width: 1280px !important; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
  border-right: 1px solid rgba(15, 23, 42, 0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] strong {
  color: #1e293b !important;
}

/* Selectbox inputs in Light mode */
div[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
}
div[data-baseweb="select"] * {
  color: #0f172a !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.4rem !important;
  background: #cbd5e1 !important;
  padding: 0.45rem !important;
  border-radius: 14px !important;
  border: 1px solid #94a3b8 !important;
}
.stTabs [data-baseweb="tab"],
.stTabs button[role="tab"],
.stTabs [data-baseweb="tab"] *,
.stTabs button[role="tab"] *,
.stTabs [data-testid="stMarkdownContainer"] p,
.stTabs [data-testid="stMarkdownContainer"] span,
.stTabs p,
.stTabs span {
  color: #0f172a !important;
  font-weight: 700 !important;
  font-size: 0.92rem !important;
  border-radius: 10px !important;
  background: transparent !important;
  border: none !important;
  opacity: 1 !important;
}
.stTabs [aria-selected="true"],
.stTabs button[role="tab"][aria-selected="true"],
.stTabs [aria-selected="true"] *,
.stTabs button[role="tab"][aria-selected="true"] *,
.stTabs [aria-selected="true"] [data-testid="stMarkdownContainer"] p,
.stTabs [aria-selected="true"] p {
  color: #0284c7 !important;
  font-weight: 800 !important;
  background: #ffffff !important;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3) !important;
  border: 1.5px solid #0284c7 !important;
  opacity: 1 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

.stButton > button {
  background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  box-shadow: 0 8px 20px rgba(2, 132, 199, 0.22) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; }

[data-testid="stMetric"] {
  background: var(--ep-surface) !important;
  border: 1px solid var(--ep-border) !important;
  border-radius: var(--ep-radius-sm) !important;
  padding: 0.85rem 1rem !important;
  box-shadow: var(--ep-shadow) !important;
}

.ep-hero {
  border-radius: 22px;
  padding: 1.75rem 1.9rem 1.5rem;
  margin-bottom: 1.25rem;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.10), rgba(13, 148, 136, 0.06)), #fff;
  border: 1px solid var(--ep-border);
  box-shadow: var(--ep-shadow);
}
.ep-hero-kicker { color: #0d9488; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.55rem; }
.ep-hero h1 {
  margin: 0 0 0.45rem 0 !important;
  font-size: clamp(1.55rem, 2.6vw, 2.05rem) !important;
  background: linear-gradient(105deg, #0f172a 0%, #0284c7 50%, #0d9488 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.ep-hero-sub { color: var(--ep-text-muted); font-size: 1rem; line-height: 1.55; margin: 0; }
.ep-hero-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.1rem; }

.ep-pill {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.28rem 0.7rem; border-radius: 999px;
  font-size: 0.78rem; font-weight: 600;
  border: 1px solid var(--ep-border); background: #f8fafc; color: var(--ep-text-muted);
}
.ep-pill--ok { color: #047857; border-color: rgba(5, 150, 105, 0.3); background: #ecfdf5; }
.ep-pill--warn { color: #b45309; border-color: rgba(217, 119, 6, 0.3); background: #fffbeb; }
.ep-pill--err { color: #b91c1c; border-color: rgba(220, 38, 38, 0.3); background: #fef2f2; }
.ep-pill--accent { color: #0369a1; border-color: rgba(2, 132, 199, 0.3); background: #e0f2fe; }

.ep-card {
  background: var(--ep-surface);
  border: 1px solid var(--ep-border);
  border-radius: var(--ep-radius);
  padding: 1.15rem 1.25rem;
  box-shadow: var(--ep-shadow);
  height: 100%;
  transition: border-color 0.25s ease, transform 0.25s ease;
}
.ep-card:hover { border-color: var(--ep-border-strong); transform: translateY(-3px); }
.ep-card-label {
  display: flex; align-items: center; gap: 0.4rem;
  font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--ep-text-muted); margin-bottom: 0.45rem;
}
.ep-card-value { font-size: 1.85rem; font-weight: 700; letter-spacing: -0.03em; color: var(--ep-text); }
.ep-card-value--solar { color: #d97706; }
.ep-card-value--wind { color: #0284c7; }
.ep-card-value--total { color: #0d9488; }
.ep-card-value--default { color: #4f46e5; }
.ep-card-hint { margin-top: 0.4rem; font-size: 0.82rem; color: var(--ep-text-muted); }

.ep-section-title {
  display: flex; align-items: center; gap: 0.55rem;
  font-size: 1.15rem; font-weight: 700; color: var(--ep-text); margin: 0.25rem 0 0.85rem 0;
}
.ep-section-title span.ep-bar {
  width: 4px; height: 1.15rem; border-radius: 4px;
  background: linear-gradient(180deg, #0284c7, #0d9488); display: inline-block;
}

.ep-module-tile {
  background: #fff; border: 1px solid var(--ep-border); border-radius: 16px;
  padding: 1.1rem 1.15rem; height: 100%;
}
.ep-module-tile h4 { margin: 0.35rem 0 !important; font-size: 1rem !important; color: var(--ep-text) !important; }
.ep-module-tile p { margin: 0; font-size: 0.86rem; color: var(--ep-text-muted); line-height: 1.45; }
.ep-module-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(13, 148, 136, 0.1));
  border: 1px solid var(--ep-border); font-size: 1.1rem;
}

.ep-footer {
  margin-top: 2.5rem; padding: 1.25rem 0 0.5rem;
  border-top: 1px solid var(--ep-border); text-align: center;
  color: var(--ep-text-muted); font-size: 0.82rem; line-height: 1.6;
}
.ep-footer strong { color: var(--ep-text); }

.ep-brand {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.35rem 0.15rem 0.85rem; border-bottom: 1px solid var(--ep-border); margin-bottom: 0.85rem;
}
.ep-brand-mark {
  width: 42px; height: 42px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; background: linear-gradient(145deg, #0284c7, #0d9488);
  color: white; font-weight: 800; box-shadow: 0 8px 18px rgba(2, 132, 199, 0.25);
}
.ep-brand-text strong { display: block; color: var(--ep-text); font-size: 1.05rem; }
.ep-brand-text span { display: block; color: var(--ep-text-muted); font-size: 0.75rem; margin-top: 0.1rem; }

.energy-card {
  background: var(--ep-surface) !important; border: 1px solid var(--ep-border) !important;
  border-radius: var(--ep-radius) !important; padding: 1.15rem !important; box-shadow: var(--ep-shadow) !important;
}
.metric-value { font-size: 1.85rem; font-weight: 700; }
.ep-icon { display: inline-block; vertical-align: -0.2em; }
.ep-icon-label { display: inline-flex; align-items: center; gap: 0.35rem; }
"""

MOBILE_CSS = r"""
.main { overflow-x: hidden !important; }
[data-testid="stAppViewContainer"] { overflow-x: hidden !important; }
img, video, canvas, iframe { max-width: 100% !important; }
.js-plotly-plot, .stDataFrame { max-width: 100% !important; }

.main .block-container {
  padding-left: max(1rem, env(safe-area-inset-left)) !important;
  padding-right: max(1rem, env(safe-area-inset-right)) !important;
}

@media (max-width: 768px) {
  .main .block-container {
    padding-top: 0.85rem !important;
    padding-bottom: 2rem !important;
  }
  .ep-hero { padding: 1.2rem 1.15rem !important; border-radius: 16px !important; }
  .ep-hero h1 { font-size: 1.35rem !important; }
  .ep-card-value { font-size: 1.45rem !important; }
  .ep-card:hover, .ep-module-tile:hover { transform: none !important; }
  .stButton > button {
    width: 100% !important;
    min-height: 44px !important;
  }
  .stButton > button:hover { transform: none !important; }
  .stTabs [data-baseweb="tab"] {
    padding: 0.45rem 0.7rem !important;
    font-size: 0.8rem !important;
  }
  [data-testid="stSidebar"] { min-width: min(88vw, 320px) !important; }
  iframe { min-height: 260px !important; max-height: 55vh !important; }
}

@media (max-width: 480px) {
  .ep-hero h1 { font-size: 1.2rem !important; }
  .ep-card-value { font-size: 1.25rem !important; }
  .ep-prediction-card { padding: 0.85rem !important; }
}
"""

# Shared component styles (empty / prediction cards)
COMPONENT_CSS = r"""
.ep-empty-state {
  text-align: center;
  padding: 2rem 1.25rem;
  border: 1px dashed var(--ep-border);
  border-radius: var(--ep-radius);
  background: var(--ep-surface);
  margin: 0.75rem 0 1.25rem;
}
.ep-empty-icon { font-size: 1.75rem; margin-bottom: 0.5rem; opacity: 0.85; }
.ep-empty-title { font-weight: 700; color: var(--ep-text); font-size: 1.05rem; }
.ep-empty-desc { color: var(--ep-text-muted); font-size: 0.9rem; margin: 0.4rem 0 0; line-height: 1.45; }

.ep-prediction-card { margin-bottom: 1rem; }
.ep-prediction-rec {
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0.35rem 0 0.75rem;
  background: linear-gradient(90deg, var(--ep-accent), var(--ep-accent-2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.ep-prediction-rows { display: flex; flex-direction: column; gap: 0.35rem; }
.ep-prediction-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 0.92rem; padding: 0.2rem 0;
  border-bottom: 1px solid var(--ep-border);
}
.ep-prediction-k { color: var(--ep-text-muted); }
.ep-prediction-v { color: var(--ep-text); font-weight: 600; font-variant-numeric: tabular-nums; }

.ep-metric-card { min-height: 7rem; }
"""


def _theme_bundle(theme: str) -> str:
    """Full CSS string for a theme (tokens vars + base + components + mobile)."""
    from dashboard.styles.tokens import get_tokens, tokens_to_css_vars

    is_light = theme.lower().startswith("light")
    base = LIGHT_CSS if is_light else DARK_CSS
    vars_block = tokens_to_css_vars(get_tokens(theme))
    return f"@import url('{_FONT_LINK}');\n{vars_block}\n{base}\n{COMPONENT_CSS}\n{MOBILE_CSS}\n"


def _ensure_theme_css_files() -> None:
    """Keep theme_*.css on disk in sync with Python CSS constants + tokens."""
    for name, theme in (("theme_dark.css", "Dark"), ("theme_light.css", "Light")):
        path = _STYLES_DIR / name
        body = _theme_bundle(theme)
        try:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                path.write_text(body, encoding="utf-8")
        except OSError:
            pass


def inject_theme(theme: str = "Dark") -> None:
    """
    Inject theme CSS cleanly into page DOM via <style> tag.
    """
    _ensure_theme_css_files()
    payload = f"<style>\n{_theme_bundle(theme)}\n</style>"
    st.markdown(payload, unsafe_allow_html=True)
    if hasattr(st, "html"):
        try:
            st.html(payload)
        except Exception:
            pass


# Backward-compatible alias used by multipage shells
ICON_CSS = ""

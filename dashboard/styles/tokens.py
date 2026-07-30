"""
EcoPredict AI — design tokens (dark / light).

Single source of truth for colors, typography, spacing, and radii.
Consumed by ``custom_css.inject_theme`` and optional Python-side theming.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

ThemeName = Literal["Dark", "Light"]


@dataclass(frozen=True)
class ColorTokens:
    bg_0: str
    bg_1: str
    bg_2: str
    surface: str
    surface_2: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    accent: str
    accent_2: str
    accent_3: str
    success: str
    warn: str
    danger: str
    solar: str
    wind: str
    grid: str


@dataclass(frozen=True)
class TypographyTokens:
    font_sans: str
    font_mono: str
    size_xs: str
    size_sm: str
    size_md: str
    size_lg: str
    size_xl: str
    size_2xl: str
    weight_regular: int
    weight_medium: int
    weight_semibold: int
    weight_bold: int


@dataclass(frozen=True)
class SpacingTokens:
    xs: str
    sm: str
    md: str
    lg: str
    xl: str
    xxl: str


@dataclass(frozen=True)
class RadiusTokens:
    sm: str
    md: str
    lg: str
    pill: str


@dataclass(frozen=True)
class ShadowTokens:
    card: str
    glow: str


@dataclass(frozen=True)
class DesignTokens:
    theme: ThemeName
    colors: ColorTokens
    typography: TypographyTokens
    spacing: SpacingTokens
    radius: RadiusTokens
    shadows: ShadowTokens
    content_max_width: str = "1280px"


TYPOGRAPHY = TypographyTokens(
    font_sans="'DM Sans', 'Segoe UI', system-ui, sans-serif",
    font_mono="'JetBrains Mono', ui-monospace, monospace",
    size_xs="0.75rem",
    size_sm="0.875rem",
    size_md="1rem",
    size_lg="1.125rem",
    size_xl="1.35rem",
    size_2xl="clamp(1.55rem, 2.6vw, 2.05rem)",
    weight_regular=400,
    weight_medium=500,
    weight_semibold=600,
    weight_bold=700,
)

SPACING = SpacingTokens(
    xs="0.25rem",
    sm="0.5rem",
    md="1rem",
    lg="1.5rem",
    xl="2rem",
    xxl="3rem",
)

RADIUS = RadiusTokens(
    sm="12px",
    md="16px",
    lg="18px",
    pill="999px",
)

DARK_COLORS = ColorTokens(
    bg_0="#070b14",
    bg_1="#0c1222",
    bg_2="#121a2e",
    surface="rgba(18, 28, 48, 0.72)",
    surface_2="rgba(24, 36, 58, 0.88)",
    border="rgba(148, 180, 220, 0.12)",
    border_strong="rgba(56, 189, 248, 0.28)",
    text="#e8eef8",
    text_muted="#8b9bb8",
    accent="#38bdf8",
    accent_2="#2dd4bf",
    accent_3="#a78bfa",
    success="#34d399",
    warn="#fbbf24",
    danger="#f87171",
    solar="#fbbf24",
    wind="#38bdf8",
    grid="#a78bfa",
)

LIGHT_COLORS = ColorTokens(
    bg_0="#f4f7fb",
    bg_1="#eef2f8",
    bg_2="#e8eef7",
    surface="rgba(255, 255, 255, 0.82)",
    surface_2="rgba(255, 255, 255, 0.92)",
    border="rgba(15, 23, 42, 0.08)",
    border_strong="rgba(14, 165, 233, 0.35)",
    text="#0f172a",
    text_muted="#64748b",
    accent="#0284c7",
    accent_2="#0d9488",
    accent_3="#7c3aed",
    success="#059669",
    warn="#d97706",
    danger="#dc2626",
    solar="#d97706",
    wind="#0284c7",
    grid="#7c3aed",
)

DARK_SHADOWS = ShadowTokens(
    card="0 12px 40px rgba(0, 0, 0, 0.35)",
    glow="0 0 40px rgba(56, 189, 248, 0.12)",
)

LIGHT_SHADOWS = ShadowTokens(
    card="0 10px 30px rgba(15, 23, 42, 0.06)",
    glow="0 0 30px rgba(14, 165, 233, 0.08)",
)


def get_tokens(theme: str = "Dark") -> DesignTokens:
    """Return design tokens for Dark or Light theme."""
    is_light = str(theme).lower().startswith("light")
    return DesignTokens(
        theme="Light" if is_light else "Dark",
        colors=LIGHT_COLORS if is_light else DARK_COLORS,
        typography=TYPOGRAPHY,
        spacing=SPACING,
        radius=RADIUS,
        shadows=LIGHT_SHADOWS if is_light else DARK_SHADOWS,
    )


def tokens_to_css_vars(tokens: DesignTokens) -> str:
    """Emit CSS custom properties block for ``:root``."""
    c = tokens.colors
    t = tokens.typography
    s = tokens.spacing
    r = tokens.radius
    sh = tokens.shadows
    return f"""
:root {{
  --ep-bg-0: {c.bg_0};
  --ep-bg-1: {c.bg_1};
  --ep-bg-2: {c.bg_2};
  --ep-surface: {c.surface};
  --ep-surface-2: {c.surface_2};
  --ep-border: {c.border};
  --ep-border-strong: {c.border_strong};
  --ep-text: {c.text};
  --ep-text-muted: {c.text_muted};
  --ep-accent: {c.accent};
  --ep-accent-2: {c.accent_2};
  --ep-accent-3: {c.accent_3};
  --ep-success: {c.success};
  --ep-warn: {c.warn};
  --ep-danger: {c.danger};
  --ep-solar: {c.solar};
  --ep-wind: {c.wind};
  --ep-grid: {c.grid};
  --ep-radius: {r.lg};
  --ep-radius-sm: {r.sm};
  --ep-radius-md: {r.md};
  --ep-radius-pill: {r.pill};
  --ep-shadow: {sh.card};
  --ep-glow: {sh.glow};
  --ep-font: {t.font_sans};
  --ep-mono: {t.font_mono};
  --ep-space-xs: {s.xs};
  --ep-space-sm: {s.sm};
  --ep-space-md: {s.md};
  --ep-space-lg: {s.lg};
  --ep-space-xl: {s.xl};
  --ep-content-max: {tokens.content_max_width};
}}
""".strip()


def plotly_layout_defaults(theme: str = "Dark") -> dict[str, Any]:
    """Default Plotly layout kwargs aligned with design tokens."""
    tok = get_tokens(theme)
    c = tok.colors
    return {
        "template": "plotly_white" if tok.theme == "Light" else "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "DM Sans, Segoe UI, sans-serif", "color": c.text},
        "margin": dict(l=40, r=20, t=50, b=40),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02),
        "colorway": [c.solar, c.wind, c.accent_2, c.accent_3, c.success, c.warn],
    }


def tokens_as_dict(theme: str = "Dark") -> dict[str, Any]:
    """Serialize tokens for debugging / tests."""
    return asdict(get_tokens(theme))

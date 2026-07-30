# Dashboard UI system

## Design tokens

[`dashboard/styles/tokens.py`](../dashboard/styles/tokens.py)

- `ColorTokens`, `TypographyTokens`, `SpacingTokens`, `RadiusTokens`, `ShadowTokens`
- `get_tokens(theme)` → dark/light
- `tokens_to_css_vars()` → CSS `:root` variables
- `plotly_layout_defaults(theme)` → Plotly layout

Theme injection: [`dashboard/styles/custom_css.py`](../dashboard/styles/custom_css.py) writes `theme_dark.css` / `theme_light.css` including token vars + component CSS + mobile rules, then loads via `st.html(path)`.

## Reusable components

| Module | Role |
|--------|------|
| `dashboard/components/metric_card.py` | Metric glass cards + `metric_row` |
| `dashboard/components/status_badge.py` | Status pills / API badge |
| `dashboard/components/prediction_card.py` | Dispatch / prediction summary |
| `dashboard/components/buttons.py` | Primary/secondary buttons + `action_row` |
| `dashboard/components/states.py` | `loading_state`, `empty_state`, `error_state`, `run_safe` |
| `dashboard/components/ui_kit.py` | Hero, section header, module tiles, footer, brand |
| `dashboard/utils/plotly_theme.py` | `apply_theme`, `themed_line` |

## Responsive rules

Media queries in `custom_css.py` (`MOBILE_CSS`):

- ≤768px: reduced hero/card padding, full-width buttons, compact tabs, shorter iframes
- ≤480px: smaller type and metric values

## Refactored pages (examples)

- `dashboard/views/overview.py` — metric_row, prediction_card, empty_state, status badges
- `dashboard/views/optimization.py` — section_header, primary_button, loading/empty/error, metric_row, themed Plotly

## Integration

```python
from dashboard.styles.custom_css import inject_theme
from dashboard.components.metric_card import metric_row
from dashboard.components.states import empty_state, error_state, loading_state

inject_theme(theme)  # after sidebar
```

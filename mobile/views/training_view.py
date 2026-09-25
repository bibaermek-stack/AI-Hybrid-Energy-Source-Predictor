"""
ML model metrics view for EcoPredict AI Mobile.

Everything here comes from GET /metrics: the paper-locked figures in
artifacts/model_metrics.json and the feature importances of the solar and wind
models /predict actually runs. The screen used to show R² 98.4%, RMSE 12.4 kW
and MAE 8.7 kW — numbers that appear nowhere in the project and contradict the
published R² 0.9967 / MAE 227 kW — plus a made-up importance list mixing solar
and wind features.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile import api_client as api_client_module
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]

# i18n keys for the models' raw training column names.
FEATURE_KEYS = {
    "IRRADIATION": "feat_irradiation",
    "AMBIENT_TEMPERATURE": "feat_ambient",
    "MODULE_TEMPERATURE": "feat_module",
    "hour": "feat_hour",
    "day": "feat_day",
    "month": "feat_month",
    "Wind Speed (m/s)": "feat_wind_speed",
    "Wind Direction (°)": "feat_wind_dir",
    "Theoretical_Power_Curve (KWh)": "feat_theoretical",
}


def build_training_view(page: ft.Page) -> ft.Control:
    """Model accuracy and feature importance, loaded from the backend."""
    c = state.colors
    t = state.text

    txt_status = ft.Text(t("loading"), size=12, color=c["text_secondary"], selectable=True)

    def metric_card(title: str, color: str) -> tuple:
        value = ft.Text("—", size=18, weight=ft.FontWeight.BOLD, color=color)
        sub = ft.Text("", size=10, color=c["text_secondary"])
        card = ft.Container(
            content=ft.Column(
                [ft.Text(title, size=11, color=c["text_secondary"]), value, sub],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=10,
            border_radius=12,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
            expand=True,
        )
        return card, value, sub

    card_rf, val_rf, sub_rf = metric_card("RandomForest R²", c["success"])
    card_xgb, val_xgb, sub_xgb = metric_card("XGBoost R²", c["primary"])
    card_lstm, val_lstm, sub_lstm = metric_card("LSTM R²", c["secondary"])
    card_map, val_map, sub_map = metric_card("YOLO11n mAP@50", c["accent"])
    card_prec, val_prec, sub_prec = metric_card("Precision", c["primary"])
    card_rec, val_rec, sub_rec = metric_card("Recall", c["secondary"])

    solar_importance = ft.Column([], spacing=8)
    wind_importance = ft.Column([], spacing=8)

    def section(title: str, body: ft.Control) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                    ft.Divider(height=1, color=c["card_border"]),
                    body,
                ],
                spacing=10,
            ),
            padding=14,
            border_radius=14,
            bgcolor=c["surface_variant"],
            border=ft.Border.all(1, c["card_border"]),
        )

    def importance_rows(items: list, color: str) -> list:
        if not items:
            return [ft.Text(t("tr_model_not_loaded"), size=12, color=c["text_secondary"])]
        rows = []
        for item in items:
            ratio = max(0.0, min(1.0, float(item.get("importance") or 0.0)))
            name = str(item.get("feature", "?"))
            rows.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(t(FEATURE_KEYS[name]) if name in FEATURE_KEYS else name, size=12, weight=ft.FontWeight.W_500),
                                ft.Text(f"{ratio * 100:.1f}%", size=12, weight=ft.FontWeight.BOLD, color=color),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        # Floor of 2 px so a near-zero feature still shows a sliver.
                        ft.Container(width=max(2.0, ratio * 260), height=8, bgcolor=color, border_radius=4),
                    ],
                    spacing=2,
                )
            )
        return rows

    def _pct(x) -> str:
        try:
            return f"{float(x) * 100:.1f}%"
        except (TypeError, ValueError):
            return "—"

    def _r2(x) -> str:
        try:
            return f"{float(x):.4f}"
        except (TypeError, ValueError):
            return "—"

    async def load() -> None:
        data = await api_client.get_metrics()
        if data is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            txt_status.value = t("tr_err_metrics", reason=reason)
            txt_status.color = c["error"]
            txt_status.visible = True
            page.update()
            return

        txt_status.visible = False
        solar = data.get("solar_forecast") or {}
        for key, val, sub in (
            ("random_forest", val_rf, sub_rf),
            ("xgboost", val_xgb, sub_xgb),
            ("lstm", val_lstm, sub_lstm),
        ):
            m = solar.get(key) or {}
            val.value = _r2(m.get("r2"))
            sub.value = t("tr_mae", mae=m["mae_kw"]) if m.get("mae_kw") is not None else ""

        test = (data.get("yolo11n") or {}).get("test") or {}
        val_map.value, sub_map.value = _pct(test.get("mAP50")), t("tr_test_images", n=test.get("images", "—"))
        val_prec.value, sub_prec.value = _pct(test.get("precision")), t("tr_test_set")
        val_rec.value, sub_rec.value = _pct(test.get("recall")), t("tr_test_set")

        importance = data.get("feature_importance") or {}
        solar_importance.controls = importance_rows(importance.get("solar") or [], c["accent"])
        wind_importance.controls = importance_rows(importance.get("wind") or [], c["secondary"])
        page.update()

    view = ft.ListView(
        controls=[
            ft.Text(t("tr_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("tr_source"), size=11, color=c["text_secondary"]),
            txt_status,
            ft.Text(t("tr_solar_heading"), size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Row([card_rf, card_xgb, card_lstm], spacing=8),
            ft.Text(t("tr_yolo_heading"), size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Row([card_map, card_prec, card_rec], spacing=8),
            section(t("tr_solar_importance"), solar_importance),
            section(t("tr_wind_importance"), wind_importance),
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
        expand=True,
    )
    # Fetched each time the tab opens (on_nav_change in main.py).
    view.data = load
    return view

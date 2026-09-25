"""
AI Energy Advisor Chat View for EcoPredict AI Mobile.

The conversation lives in state.chat_history, so rebuilding this view after a
language or theme switch redraws the same messages instead of wiping them.
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


def build_chat_view(page: ft.Page) -> ft.Control:
    """Build AI Advisor chat view with message bubbles & suggestion chips."""
    c = state.colors
    t = state.text

    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    def bubble(role: str, text: str) -> ft.Control:
        if role == "user":
            return ft.Container(
                content=ft.Text(text, size=13, color="#FFFFFF", selectable=True),
                padding=12,
                border_radius=14,
                bgcolor=c["primary"],
                alignment=ft.Alignment.TOP_RIGHT,
            )
        if role == "error":
            return ft.Container(
                content=ft.Text(text, size=12, color=c["error"], selectable=True),
                padding=10,
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.08, c["error"]),
                border=ft.Border.all(1, c["error"]),
            )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.Icons.SMART_TOY, color=c["primary"], size=16), ft.Text("EcoPredict AI", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])]),
                    ft.Text(text, size=13, color=c["text_primary"], selectable=True),
                ],
                spacing=4,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
        )

    welcome_bubble = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SMART_TOY, color=c["primary"], size=18),
                        ft.Text("EcoPredict AI Advisor", size=12, weight=ft.FontWeight.BOLD, color=c["primary"]),
                    ],
                    spacing=6,
                ),
                ft.Text(t("chat_welcome"), size=13, color=c["text_primary"]),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface_variant"],
        alignment=ft.Alignment.TOP_LEFT,
    )
    chat_list.controls.append(welcome_bubble)
    chat_list.controls.extend(bubble(role, text) for role, text in state.chat_history)

    tf_prompt = ft.TextField(
        hint_text=t("chat_placeholder"),
        expand=True,
        border_radius=20,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=10),
    )

    def add(role: str, text: str) -> None:
        state.chat_history.append((role, text))
        chat_list.controls.append(bubble(role, text))

    async def send_message(prompt_text: str):
        prompt_text = (prompt_text or "").strip()
        if not prompt_text:
            return

        add("user", prompt_text)
        tf_prompt.value = ""
        loading_card = ft.Container(
            content=ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2), ft.Text(t("chat_thinking"), size=12, color=c["text_secondary"])]),
            padding=10,
        )
        chat_list.controls.append(loading_card)
        page.update()

        reply = await api_client.chat(prompt_text)
        chat_list.controls.remove(loading_card)
        if reply is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            add("error", t("chat_err_offline", reason=reason))
        else:
            add("ai", reply or t("chat_empty_reply"))
        page.update()

    async def on_send_click(e):
        await send_message(tf_prompt.value)

    tf_prompt.on_submit = on_send_click

    def make_chip(text_key: str):
        txt = t(text_key)
        return ft.Chip(
            label=ft.Text(txt, size=11),
            on_click=lambda e: page.run_task(send_message, txt),
            bgcolor=c["surface"],
        )

    chips_row = ft.Row(
        [make_chip("chat_chip1"), make_chip("chat_chip2"), make_chip("chat_chip3")],
        scroll=ft.ScrollMode.AUTO,
    )

    input_bar = ft.Row(
        [
            tf_prompt,
            ft.IconButton(
                icon=ft.Icons.SEND_ROUNDED,
                icon_color=c["primary"],
                tooltip=t("chat_send"),
                on_click=on_send_click,
            ),
        ],
        spacing=8,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("💬 " + t("chat_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ft.Container(content=chat_list, expand=True),
                chips_row,
                ft.Container(height=4),
                input_bar,
            ],
            expand=True,
            spacing=8,
        ),
        expand=True,
        padding=12,
    )

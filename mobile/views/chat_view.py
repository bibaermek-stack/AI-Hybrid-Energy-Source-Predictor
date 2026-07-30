"""
AI Energy Advisor Chat View for EcoPredict AI Mobile.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_chat_view(page: ft.Page) -> ft.Control:
    """Build AI Advisor chat view with message bubbles & suggestion chips."""
    c = state.colors

    # Chat history ListView
    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    # Welcome message bubble
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
                ft.Text(state.text("chat_welcome"), size=13, color=c["text_primary"]),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface_variant"],
        alignment=ft.Alignment.TOP_LEFT,
    )
    chat_list.controls.append(welcome_bubble)

    tf_prompt = ft.TextField(
        hint_text=state.text("chat_placeholder"),
        expand=True,
        border_radius=20,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=10),
    )

    async def send_message(prompt_text: str):
        if not prompt_text.strip():
            return

        # Render user bubble
        user_bubble = ft.Container(
            content=ft.Text(prompt_text, size=13, color="#FFFFFF"),
            padding=12,
            border_radius=14,
            bgcolor=c["primary"],
            alignment=ft.Alignment.TOP_RIGHT,
        )
        chat_list.controls.append(user_bubble)
        tf_prompt.value = ""
        page.update()

        # Render loading indicator
        loading_card = ft.Container(
            content=ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2), ft.Text("Thinking...", size=12, color=c["text_secondary"])]),
            padding=10,
        )
        chat_list.controls.append(loading_card)
        page.update()

        # Call API
        reply = await api_client.chat(prompt_text)

        chat_list.controls.remove(loading_card)

        # Render AI response bubble
        ai_bubble = ft.Container(
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.Icons.SMART_TOY, color=c["primary"], size=16), ft.Text("EcoPredict AI", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])]),
                    ft.Text(reply, size=13, color=c["text_primary"]),
                ],
                spacing=4,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
        )
        chat_list.controls.append(ai_bubble)
        page.update()

    async def on_send_click(e):
        await send_message(tf_prompt.value)

    # Suggestion Chips
    def make_chip(text_key: str):
        txt = state.text(text_key)
        return ft.Chip(
            label=ft.Text(txt, size=11),
            on_click=lambda e: page.run_task(send_message, txt),
            bgcolor=c["surface"],
        )

    chips_row = ft.Row(
        [
            make_chip("chat_chip1"),
            make_chip("chat_chip2"),
            make_chip("chat_chip3"),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    input_bar = ft.Row(
        [
            tf_prompt,
            ft.IconButton(
                icon=ft.Icons.SEND_ROUNDED,
                icon_color=c["primary"],
                on_click=on_send_click,
            ),
        ],
        spacing=8,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("💬 " + state.text("chat_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
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

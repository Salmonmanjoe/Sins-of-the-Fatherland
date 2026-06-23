"""ARIA Chat tab widget — dedicated AI conversation pane."""
from __future__ import annotations
import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, RichLog, Static
from rich.text import Text


class ARIAChatApp(Widget):
    DEFAULT_CSS = """
    ARIAChatApp { height: 1fr; }
    ARIAChatApp > Vertical { height: 1fr; }
    #chat-header {
        height: 1;
        background: #1a0030;
        color: #cc88ff;
        padding: 0 1;
    }
    #chat-log {
        border: round #3d0070;
        background: #050510;
        height: 1fr;
    }
    #chat-thinking {
        height: 1;
        color: #aa66ff;
        padding: 0 1;
    }
    #chat-toolbar { height: 3; align: left middle; }
    #chat-prompt-label { width: auto; color: #cc88ff; padding: 0 1; }
    #chat-input { width: 1fr; border: round #3d0070; }
    #chat-input:focus { border: round #cc88ff; }
    #btn-reset { min-width: 10; margin-left: 1; }
    """

    @property
    def ai(self):
        return self.app.ai

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "  🤖  ARIA — Artificial Reasoning & Intelligence Assistant",
                id="chat-header", markup=True
            )
            yield RichLog(id="chat-log", markup=True, highlight=True, wrap=True)
            yield Static("", id="chat-thinking", markup=True)
            with Horizontal(id="chat-toolbar"):
                yield Static("ARIA ▸", id="chat-prompt-label")
                yield Input(placeholder="Ask ARIA anything…", id="chat-input")
                yield Button("⟳ Reset", id="btn-reset", variant="warning")

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write(Text.from_markup(
            "[bold #cc88ff]ARIA online.[/] Ask me anything — I can help with code, "
            "files, questions, or just chat.\n"
            "[dim]Type your message below. Use [bold]⟳ Reset[/] to clear conversation history.[/]"
        ))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-reset":
            self.ai.reset()
            log = self.query_one("#chat-log", RichLog)
            log.clear()
            log.write(Text.from_markup("[yellow]ARIA memory cleared — fresh conversation.[/]"))

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "chat-input":
            return
        event.stop()
        prompt = event.value.strip()
        if not prompt:
            return
        self.query_one("#chat-input", Input).clear()
        log = self.query_one("#chat-log", RichLog)
        thinking = self.query_one("#chat-thinking", Static)

        log.write(Text.from_markup(f"[bold white]You ▸[/] {prompt}"))
        asyncio.create_task(self._ask_aria(prompt, log, thinking))

    async def _ask_aria(self, prompt: str, log: RichLog, thinking: Static) -> None:
        thinking.update("[bold #cc88ff]ARIA is thinking…  ▌[/]")
        self.query_one("#chat-input", Input).disabled = True
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.ai.chat, prompt)
            thinking.update("")
            log.write(Text.from_markup(f"[bold #cc88ff]ARIA ▸[/] {response}"))
        except Exception as e:
            thinking.update("")
            log.write(Text.from_markup(f"[red]ARIA error: {e}[/]"))
        finally:
            self.query_one("#chat-input", Input).disabled = False
            self.query_one("#chat-input", Input).focus()

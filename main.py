"""
Growther Agent — CLI Entry Point

Run this file to interact with your personal YouTube monetization coach.

Usage:
    python main.py                    # Interactive chat mode
    python main.py --analyze          # Full channel analysis (guided prompts)
    python main.py --demo             # Run a demo analysis with sample data
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.rule import Rule
from rich.text import Text

from agent import GrowtherAgent

load_dotenv()
console = Console()


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_banner():
    console.print(
        Panel.fit(
            "[bold yellow]Growther Agent[/bold yellow]\n"
            "[dim]Your AI-powered YouTube Monetization Coach[/dim]\n"
            "[dim]Powered by Claude Opus 4.6[/dim]",
            border_style="yellow",
        )
    )
    console.print()


def stream_response(agent: GrowtherAgent, message: str):
    """Stream Claude's response to the console, rendering markdown at the end."""
    console.print(Rule("[yellow]Growther Agent[/yellow]"))
    collected = []
    with console.status("[yellow]Thinking...[/yellow]", spinner="dots"):
        first_chunk = True
        for chunk in agent.chat(message):
            if first_chunk:
                console.print()  # newline after spinner clears
                first_chunk = False
            collected.append(chunk)
            # Print tool-use notices directly; buffer the rest
            if chunk.startswith("\n\n> **[Tool:"):
                console.print(Text(chunk.strip(), style="dim cyan"))

    # Render the final assembled text as Markdown
    full_response = "".join(collected)
    # Strip tool notices (already printed above)
    import re
    clean = re.sub(r"\n\n> \*\*\[Tool:.*?\]\*\*.*?\n\n", "\n", full_response, flags=re.DOTALL)
    console.print(Markdown(clean))
    console.print()


# ---------------------------------------------------------------------------
# Guided analysis flow
# ---------------------------------------------------------------------------

def guided_analysis(agent: GrowtherAgent):
    """Walk the user through a series of prompts to collect channel data."""
    console.print(Panel("[bold]Channel Analysis Setup[/bold]", style="yellow"))
    console.print(
        "[dim]I'll collect some information about your channel so I can give you a personalized monetization plan.[/dim]\n"
    )

    channel_name = Prompt.ask("[bold]Channel name[/bold]")
    niche = Prompt.ask("[bold]Content niche[/bold]", default="general")
    target_audience = Prompt.ask(
        "[bold]Target audience[/bold]",
        default=f"People interested in {niche}",
    )
    subscribers = IntPrompt.ask("[bold]Current subscribers[/bold]", default=0)
    watch_hours = IntPrompt.ask(
        "[bold]Watch hours (last 12 months)[/bold]", default=0
    )
    weekly_sub_growth = IntPrompt.ask(
        "[bold]Average new subscribers per week[/bold]", default=5
    )
    weekly_watch_hours = IntPrompt.ask(
        "[bold]Average watch hours per week[/bold]", default=20
    )
    uploads_per_week = IntPrompt.ask(
        "[bold]Videos uploaded per week[/bold]", default=1
    )
    uses_shorts = Confirm.ask("[bold]Do you publish YouTube Shorts?[/bold]", default=False)

    shorts_views_90d = 0
    weekly_shorts_views = 0
    if uses_shorts:
        shorts_views_90d = IntPrompt.ask(
            "[bold]Shorts views (last 90 days)[/bold]", default=0
        )
        weekly_shorts_views = IntPrompt.ask(
            "[bold]Average Shorts views per week[/bold]", default=0
        )

    strengths_raw = Prompt.ask(
        "[bold]Your content strengths[/bold] (comma-separated, e.g. editing, storytelling)",
        default="",
    )
    content_strengths = [s.strip() for s in strengths_raw.split(",") if s.strip()]

    console.print()
    console.print("[yellow]Running full monetization analysis...[/yellow]")
    console.print(Rule())

    result = agent.analyze_channel(
        channel_name=channel_name,
        niche=niche,
        subscribers=subscribers,
        watch_hours=float(watch_hours),
        weekly_sub_growth=weekly_sub_growth,
        weekly_watch_hours=float(weekly_watch_hours),
        uploads_per_week=uploads_per_week,
        uses_shorts=uses_shorts,
        shorts_views_90d=shorts_views_90d,
        weekly_shorts_views=weekly_shorts_views,
        target_audience=target_audience,
        content_strengths=content_strengths,
    )

    console.print(Markdown(result))


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

def run_demo(agent: GrowtherAgent):
    """Run a demo analysis with fictional channel data."""
    console.print(
        Panel(
            "[bold]Demo Mode[/bold] — Analyzing a fictional channel: [italic]TechSimplified[/italic]",
            style="cyan",
        )
    )
    console.print()

    result = agent.analyze_channel(
        channel_name="TechSimplified",
        niche="consumer tech reviews and tutorials",
        subscribers=612,
        watch_hours=1_850.0,
        weekly_sub_growth=28,
        weekly_watch_hours=120.0,
        uploads_per_week=2,
        uses_shorts=True,
        shorts_views_90d=450_000,
        weekly_shorts_views=35_000,
        target_audience="tech-curious people aged 18-40 who want honest product reviews",
        content_strengths=["clear explanations", "video editing", "product photography"],
    )

    console.print(Markdown(result))


# ---------------------------------------------------------------------------
# Interactive chat mode
# ---------------------------------------------------------------------------

def interactive_chat(agent: GrowtherAgent):
    """Open-ended conversational mode."""
    console.print(
        "[dim]Ask me anything about growing and monetizing your YouTube channel.[/dim]"
    )
    console.print("[dim]Type [bold]exit[/bold] or [bold]quit[/bold] to leave. "
                  "Type [bold]reset[/bold] to start a new conversation.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        cmd = user_input.strip().lower()
        if cmd in ("exit", "quit", "q"):
            console.print("[dim]Thanks for using Growther Agent. Good luck with your channel![/dim]")
            break
        if cmd == "reset":
            agent.reset()
            console.print("[yellow]Conversation reset.[/yellow]\n")
            continue

        stream_response(agent, user_input)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Growther Agent — YouTube Monetization Coach"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run a guided channel analysis with step-by-step prompts.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo analysis with a fictional channel.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY environment variable is not set.\n"
            "Copy [bold].env.example[/bold] to [bold].env[/bold] and add your API key."
        )
        sys.exit(1)

    print_banner()
    agent = GrowtherAgent(api_key=api_key)

    if args.analyze:
        guided_analysis(agent)
    elif args.demo:
        run_demo(agent)
    else:
        interactive_chat(agent)


if __name__ == "__main__":
    main()

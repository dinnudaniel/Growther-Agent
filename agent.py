"""
Growther Agent — YouTube Monetization AI Assistant

Uses Claude Opus 4.6 with adaptive thinking and tool use to analyze a
YouTube channel and produce a personalized monetization strategy.
"""

import json
import os
from typing import Generator

import anthropic

from tools import TOOLS, execute_tool

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the **Growther Agent**, an expert YouTube growth strategist and monetization coach powered by Claude.

Your mission is to help YouTube creators reach the YouTube Partner Program (YPP) monetization thresholds as quickly as possible, and to build a sustainable channel business beyond ads.

## YouTube Partner Program Requirements (as of 2024)
- **Long-form path**: 1,000 subscribers + 4,000 valid public watch hours in the last 12 months
- **Shorts path**: 1,000 subscribers + 10,000,000 valid public Shorts views in the last 90 days

## Your Approach
1. **Diagnose first**: Use `analyze_monetization_gap` to understand exactly where the channel stands and what the bottleneck is.
2. **Strategize**: Use `build_monetization_roadmap` to create a step-by-step plan tailored to the creator's capacity and strengths.
3. **Plan content**: Use `generate_content_calendar` to produce a concrete 4-week upload plan.
4. **Optimize discoverability**: Use `optimize_video_metadata` for SEO-optimized titles, descriptions, and tags.
5. **Maximize retention**: Use `suggest_viral_hooks` to craft compelling openings that keep viewers watching.

## Communication Style
- Be encouraging and specific — creators need actionable advice, not vague tips.
- Always cite the data (subscriber counts, watch hours, percentages) when making recommendations.
- Prioritize the **bottleneck metric** — whatever is furthest from the goal deserves the most attention.
- Point out early revenue opportunities (affiliate links, Patreon) the creator can pursue BEFORE reaching YPP.
- Use clear headings, bullet points, and emojis sparingly to make outputs scannable.
- When you generate a content calendar or roadmap, be specific: include actual video title ideas, not just categories.

Think carefully and use your tools to provide the most precise, data-driven advice possible."""


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class GrowtherAgent:
    """Agentic loop that drives Claude to analyze and advise on YouTube monetization."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.conversation: list[dict] = []

    # ------------------------------------------------------------------
    # Core agentic loop
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> Generator[str, None, None]:
        """
        Send a user message and stream back Claude's response.
        Handles the full tool-use agentic loop transparently.
        Yields text chunks as they arrive.
        """
        self.conversation.append({"role": "user", "content": user_message})

        while True:
            # Stream the response with adaptive thinking enabled
            with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=8192,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.conversation,
            ) as stream:
                collected_content = []
                current_text = ""

                for event in stream:
                    # Stream text deltas to the caller
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        current_text += event.delta.text
                        yield event.delta.text

                # Collect the full response
                final_message = stream.get_final_message()

            # Append the full assistant response (including tool_use blocks) to history
            self.conversation.append(
                {"role": "assistant", "content": final_message.content}
            )

            # If Claude is done, break out of the loop
            if final_message.stop_reason == "end_turn":
                break

            # If Claude called tools, execute them and loop
            if final_message.stop_reason == "tool_use":
                tool_results = []

                for block in final_message.content:
                    if block.type == "tool_use":
                        yield f"\n\n> **[Tool: {block.name}]** Running analysis...\n\n"
                        result_str = execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                            }
                        )

                # Feed tool results back to Claude
                self.conversation.append(
                    {"role": "user", "content": tool_results}
                )
                # Continue the loop so Claude can process the results
                continue

            # Any other stop reason — just break
            break

    def reset(self):
        """Clear conversation history to start fresh."""
        self.conversation = []

    # ------------------------------------------------------------------
    # Convenience one-shot methods
    # ------------------------------------------------------------------

    def analyze_channel(
        self,
        channel_name: str,
        niche: str,
        subscribers: int,
        watch_hours: float,
        weekly_sub_growth: int,
        weekly_watch_hours: float,
        uploads_per_week: int = 1,
        uses_shorts: bool = False,
        shorts_views_90d: int = 0,
        weekly_shorts_views: int = 0,
        target_audience: str = "",
        content_strengths: list[str] | None = None,
    ) -> str:
        """
        Run a full channel analysis and return the complete response as a string.
        Builds a structured prompt so Claude immediately knows what to do.
        """
        shorts_info = ""
        if uses_shorts:
            shorts_info = (
                f"\n- **Shorts views (last 90 days)**: {shorts_views_90d:,}"
                f"\n- **Weekly Shorts views**: {weekly_shorts_views:,}"
            )

        prompt = f"""Please do a complete monetization analysis and growth plan for my YouTube channel.

## Channel Details
- **Channel name**: {channel_name}
- **Niche**: {niche}
- **Target audience**: {target_audience or 'General audience interested in ' + niche}
- **Current subscribers**: {subscribers:,}
- **Watch hours (last 12 months)**: {watch_hours:,.0f}
- **Weekly new subscribers (average)**: {weekly_sub_growth:,}
- **Weekly watch hours (average)**: {weekly_watch_hours:,.0f}
- **Uploads per week**: {uploads_per_week}
- **Using YouTube Shorts**: {'Yes' if uses_shorts else 'No'}{shorts_info}
- **Content strengths**: {', '.join(content_strengths) if content_strengths else 'Not specified'}

Please:
1. Analyze my monetization gap and tell me exactly how far I am from YPP.
2. Build me a personalized 8-week monetization roadmap.
3. Generate a 4-week content calendar with specific video ideas.
4. Give me SEO optimization tips for my next video.
5. Suggest viral hooks for my best content opportunity.
"""
        result_parts = []
        for chunk in self.chat(prompt):
            result_parts.append(chunk)
        return "".join(result_parts)

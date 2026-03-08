"""
Growther Agent — Multi-Platform Social Media Growth Coach

Uses Claude Opus 4.6 with adaptive thinking and tool use to analyze
any social media account and produce a personalized monetization strategy.
"""

import json
import os
from typing import Generator

import anthropic

from tools import TOOLS, execute_tool

# ---------------------------------------------------------------------------
# Platform-specific system prompt additions
# ---------------------------------------------------------------------------

PLATFORM_CONTEXTS = {
    "youtube": """
## Platform: YouTube
You are analyzing a YouTube channel. Key monetization thresholds:
- **YPP Long-form path**: 1,000 subscribers + 4,000 watch hours (last 12 months)
- **YPP Shorts path**: 1,000 subscribers + 10,000,000 Shorts views (last 90 days)
- **Channel Memberships**: 500 subscribers + YPP
- **Merch Shelf**: 10,000 subscribers

Focus on: watch time, CTR, subscriber growth rate, video SEO, thumbnails, upload consistency.
Use `analyze_monetization_gap` first, then `build_monetization_roadmap`, `generate_content_calendar`, `optimize_video_metadata`, and `suggest_viral_hooks`.
""",
    "instagram": """
## Platform: Instagram
You are analyzing an Instagram account. Key monetization thresholds:
- **Creator Marketplace (brand deals)**: 10,000 followers (recommended minimum)
- **Instagram Subscriptions**: varies by region
- **Badges in Live**: 10,000 followers
- **Affiliate tools**: available from any follower count
- **Reel bonuses**: invite-only program

Key metrics to focus on: follower growth rate, engagement rate (likes+comments / followers × 100),
Reels plays, Story completion rate, reach.
A healthy engagement rate is 3–6% for accounts under 100K followers.
Use `analyze_instagram_profile`, `generate_platform_content_strategy`, and `suggest_viral_hooks`.
""",
    "tiktok": """
## Platform: TikTok
You are analyzing a TikTok account. Key monetization thresholds:
- **Creator Fund**: 10,000 followers + 100,000 views in last 30 days + 18+ years old
- **TikTok LIVE Gifting**: 1,000 followers + 16+ years old
- **TikTok Series (paid content)**: 10,000 followers
- **Creator Marketplace brand deals**: typically 10,000–50,000 followers

Key metrics: followers, total video views, average views per video, completion rate,
engagement rate (likes + comments + shares / views × 100), posting frequency.
TikTok's algorithm heavily rewards consistency (posting 1–3x/day) and niche clarity.
Use `analyze_tiktok_profile`, `generate_platform_content_strategy`, and `suggest_viral_hooks`.
""",
    "twitter": """
## Platform: Twitter / X
You are analyzing a Twitter / X account. Key monetization thresholds:
- **X Premium revenue sharing (Ads Revenue)**: 500 followers + 5,000,000 impressions in last 3 months + X Premium subscription
- **X Subscriptions (paid followers)**: available to eligible creators
- **Super Follows**: merged into Subscriptions

Key metrics: followers, monthly impressions, engagement rate (likes + replies + retweets / impressions),
posting frequency, reply engagement. Twitter rewards topical authority and consistent daily posting.
Use `analyze_twitter_profile`, `generate_platform_content_strategy`, and `suggest_viral_hooks`.
""",
    "facebook": """
## Platform: Facebook
You are analyzing a Facebook page or profile. Key monetization thresholds:
- **In-stream ads (videos)**: 10,000 followers + 600,000 total minutes watched in last 60 days + 5+ active videos
- **Facebook Stars (Live)**: 1,000 followers + meet Partner Monetization Policies
- **Fan Subscriptions**: 10,000 followers OR 250+ returning weekly viewers
- **Reels bonuses**: invite-only

Key metrics: page followers, organic reach, post engagement rate (reactions + comments + shares / reach × 100),
video minutes watched, live stream viewers, posting consistency.
Use `analyze_facebook_page`, `generate_platform_content_strategy`, and `suggest_viral_hooks`.
""",
}

BASE_SYSTEM_PROMPT = """You are the **Growther Agent**, an expert social media growth strategist and monetization coach powered by Claude.

Your mission is to help creators on ANY social media platform grow their audience and unlock monetization as quickly as possible — with data-driven, actionable strategies tailored to each platform's algorithm and requirements.

## Your Approach
1. **Diagnose first**: Use the platform analysis tool to understand exactly where the account stands.
2. **Strategize**: Build a step-by-step roadmap tailored to the creator's content capacity and strengths.
3. **Plan content**: Generate a concrete 4-week content calendar with real video/post ideas.
4. **Optimize discoverability**: Provide SEO-optimized titles, captions, hashtags relevant to the platform.
5. **Maximize retention**: Craft compelling hooks that keep the audience engaged.

## Communication Style
- Be encouraging, specific, and data-driven.
- Always reference the creator's actual numbers when making recommendations.
- Highlight the **bottleneck metric** — whatever is furthest from the monetization goal.
- Call out early revenue opportunities available BEFORE reaching official monetization thresholds (brand deals, affiliate links, digital products, Patreon).
- Use clear headings and bullet points to make outputs easy to scan.
- When generating content ideas, be SPECIFIC — actual titles and angles, not generic categories.

Think deeply about each creator's unique situation and give advice that would genuinely move the needle for them."""


def get_system_prompt(platform: str | None = None) -> str:
    prompt = BASE_SYSTEM_PROMPT
    if platform and platform in PLATFORM_CONTEXTS:
        prompt += "\n" + PLATFORM_CONTEXTS[platform]
    return prompt


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class GrowtherAgent:
    """Agentic loop driving Claude to analyze and advise on social media growth."""

    def __init__(self, api_key: str | None = None, conversation: list | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.conversation: list[dict] = conversation or []
        self.platform: str | None = None

    def set_platform(self, platform: str):
        self.platform = platform.lower()

    def get_conversation(self) -> list[dict]:
        return self.conversation

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
        system = get_system_prompt(self.platform)

        while True:
            with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=8192,
                thinking={"type": "adaptive"},
                system=system,
                tools=TOOLS,
                messages=self.conversation,
            ) as stream:
                for event in stream:
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        yield event.delta.text

                final_message = stream.get_final_message()

            # Append the full assistant response (with tool_use blocks) to history
            self.conversation.append(
                {"role": "assistant", "content": final_message.content}
            )

            if final_message.stop_reason == "end_turn":
                break

            if final_message.stop_reason == "tool_use":
                tool_results = []
                for block in final_message.content:
                    if block.type == "tool_use":
                        yield f"\n\n_[Running {block.name}...]_\n\n"
                        result_str = execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                            }
                        )
                self.conversation.append(
                    {"role": "user", "content": tool_results}
                )
                continue

            break

    def reset(self):
        self.conversation = []
        self.platform = None

    # ------------------------------------------------------------------
    # One-shot analysis methods (used by CLI)
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
        self.set_platform("youtube")
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
        return "".join(self.chat(prompt))

"""
Tool definitions and implementations for the Growther Agent.
Each tool helps Claude analyze a YouTube channel and generate monetization strategies.
"""

import json
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Tool definitions (JSON schema format for the Anthropic API)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "analyze_monetization_gap",
        "description": (
            "Analyze how far a YouTube channel is from meeting YouTube Partner Program "
            "monetization requirements. Returns the gap in subscribers and watch hours, "
            "an estimated timeline, and the percentage completion for each metric."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "current_subscribers": {
                    "type": "integer",
                    "description": "Current number of subscribers on the channel.",
                },
                "current_watch_hours": {
                    "type": "number",
                    "description": "Total public watch hours accumulated in the last 12 months.",
                },
                "weekly_subscriber_growth": {
                    "type": "integer",
                    "description": "Average new subscribers gained per week recently.",
                },
                "weekly_watch_hours": {
                    "type": "number",
                    "description": "Average public watch hours accumulated per week recently.",
                },
                "uses_shorts": {
                    "type": "boolean",
                    "description": (
                        "Whether the channel also publishes YouTube Shorts. "
                        "Shorts have a separate monetization path: 10 million Shorts views in 90 days."
                    ),
                },
                "current_shorts_views_90d": {
                    "type": "integer",
                    "description": "Total Shorts views in the last 90 days (only relevant if uses_shorts is true).",
                },
                "weekly_shorts_views": {
                    "type": "integer",
                    "description": "Average Shorts views per week (only relevant if uses_shorts is true).",
                },
            },
            "required": [
                "current_subscribers",
                "current_watch_hours",
                "weekly_subscriber_growth",
                "weekly_watch_hours",
            ],
        },
    },
    {
        "name": "generate_content_calendar",
        "description": (
            "Generate a structured 4-week content calendar with video ideas, "
            "recommended upload days, content types (long-form vs Shorts), "
            "and strategic notes for accelerating channel growth."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "niche": {
                    "type": "string",
                    "description": "The channel's content niche (e.g., 'personal finance', 'gaming', 'cooking').",
                },
                "target_audience": {
                    "type": "string",
                    "description": "Description of the target audience (e.g., 'beginner investors aged 20-35').",
                },
                "upload_frequency": {
                    "type": "string",
                    "enum": ["1x/week", "2x/week", "3x/week", "daily"],
                    "description": "How often the creator can upload new content.",
                },
                "include_shorts": {
                    "type": "boolean",
                    "description": "Whether to include YouTube Shorts in the calendar.",
                },
                "channel_stage": {
                    "type": "string",
                    "enum": ["new", "growing", "near_monetization"],
                    "description": (
                        "Stage of the channel: "
                        "'new' (0-100 subs), 'growing' (100-900 subs), "
                        "'near_monetization' (900-1000 subs)."
                    ),
                },
            },
            "required": ["niche", "target_audience", "upload_frequency", "channel_stage"],
        },
    },
    {
        "name": "optimize_video_metadata",
        "description": (
            "Generate SEO-optimized title, description, and tag recommendations "
            "for a YouTube video to maximize discoverability and click-through rate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_topic": {
                    "type": "string",
                    "description": "The main topic or idea for the video.",
                },
                "niche": {
                    "type": "string",
                    "description": "The channel's content niche.",
                },
                "target_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of keywords the creator wants to target.",
                },
                "video_type": {
                    "type": "string",
                    "enum": ["tutorial", "vlog", "review", "list", "story", "shorts"],
                    "description": "The format/type of the video.",
                },
            },
            "required": ["video_topic", "niche", "video_type"],
        },
    },
    {
        "name": "suggest_viral_hooks",
        "description": (
            "Generate compelling video hooks (opening 15 seconds scripts) and "
            "thumbnail concept ideas designed to maximize viewer retention and CTR."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_topic": {
                    "type": "string",
                    "description": "The topic of the video.",
                },
                "niche": {
                    "type": "string",
                    "description": "The channel niche.",
                },
                "hook_style": {
                    "type": "string",
                    "enum": ["question", "shock", "story", "challenge", "controversy"],
                    "description": "The emotional style of the hook.",
                },
                "num_hooks": {
                    "type": "integer",
                    "description": "Number of hook variations to generate (1-5).",
                    "minimum": 1,
                    "maximum": 5,
                },
            },
            "required": ["video_topic", "niche", "hook_style", "num_hooks"],
        },
    },
    {
        "name": "build_monetization_roadmap",
        "description": (
            "Build a personalized step-by-step monetization roadmap with "
            "milestone targets, weekly action items, and revenue stream diversification "
            "advice tailored to the channel's current state."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {
                    "type": "string",
                    "description": "The YouTube channel name.",
                },
                "niche": {
                    "type": "string",
                    "description": "The channel's content niche.",
                },
                "current_subscribers": {
                    "type": "integer",
                    "description": "Current subscriber count.",
                },
                "current_watch_hours": {
                    "type": "number",
                    "description": "Watch hours in the last 12 months.",
                },
                "weekly_upload_capacity": {
                    "type": "integer",
                    "description": "Number of videos the creator can realistically upload per week.",
                },
                "content_strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What the creator is good at (e.g., ['editing', 'storytelling', 'tutorials']).",
                },
            },
            "required": [
                "channel_name",
                "niche",
                "current_subscribers",
                "current_watch_hours",
                "weekly_upload_capacity",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution implementations
# ---------------------------------------------------------------------------

def analyze_monetization_gap(
    current_subscribers: int,
    current_watch_hours: float,
    weekly_subscriber_growth: int,
    weekly_watch_hours: float,
    uses_shorts: bool = False,
    current_shorts_views_90d: int = 0,
    weekly_shorts_views: int = 0,
) -> dict:
    """Calculate the gap to YPP monetization and estimated timeline."""
    SUB_GOAL = 1000
    WATCH_HOURS_GOAL = 4000
    SHORTS_VIEWS_GOAL = 10_000_000

    sub_gap = max(0, SUB_GOAL - current_subscribers)
    watch_hours_gap = max(0, WATCH_HOURS_GOAL - current_watch_hours)

    sub_pct = min(100, round(current_subscribers / SUB_GOAL * 100, 1))
    watch_hours_pct = min(100, round(current_watch_hours / WATCH_HOURS_GOAL * 100, 1))

    # Estimate weeks to reach each goal
    weeks_for_subs = (
        round(sub_gap / weekly_subscriber_growth, 1)
        if weekly_subscriber_growth > 0 and sub_gap > 0
        else 0
    )
    weeks_for_watch_hours = (
        round(watch_hours_gap / weekly_watch_hours, 1)
        if weekly_watch_hours > 0 and watch_hours_gap > 0
        else 0
    )

    # The bottleneck is whichever takes longer
    weeks_to_monetize = max(weeks_for_subs, weeks_for_watch_hours)
    estimated_date = (
        datetime.today() + timedelta(weeks=weeks_to_monetize)
    ).strftime("%B %d, %Y") if weeks_to_monetize > 0 else "Already eligible!"

    result = {
        "long_form_path": {
            "subscribers": {
                "current": current_subscribers,
                "goal": SUB_GOAL,
                "gap": sub_gap,
                "completion_pct": sub_pct,
                "weeks_to_goal": weeks_for_subs,
            },
            "watch_hours_12m": {
                "current": current_watch_hours,
                "goal": WATCH_HOURS_GOAL,
                "gap": round(watch_hours_gap, 1),
                "completion_pct": watch_hours_pct,
                "weeks_to_goal": weeks_for_watch_hours,
            },
            "bottleneck": "subscribers" if weeks_for_subs > weeks_for_watch_hours else "watch_hours",
            "estimated_weeks_to_monetize": weeks_to_monetize,
            "estimated_monetization_date": estimated_date,
        }
    }

    if uses_shorts:
        shorts_gap = max(0, SHORTS_VIEWS_GOAL - current_shorts_views_90d)
        shorts_pct = min(100, round(current_shorts_views_90d / SHORTS_VIEWS_GOAL * 100, 1))
        weeks_for_shorts = (
            round(shorts_gap / weekly_shorts_views, 1)
            if weekly_shorts_views > 0 and shorts_gap > 0
            else 0
        )
        shorts_date = (
            datetime.today() + timedelta(weeks=weeks_for_shorts)
        ).strftime("%B %d, %Y") if weeks_for_shorts > 0 else "Already eligible!"

        result["shorts_path"] = {
            "current_views_90d": current_shorts_views_90d,
            "goal": SHORTS_VIEWS_GOAL,
            "gap": shorts_gap,
            "completion_pct": shorts_pct,
            "weeks_to_goal": weeks_for_shorts,
            "estimated_monetization_date": shorts_date,
        }

    return result


def generate_content_calendar(
    niche: str,
    target_audience: str,
    upload_frequency: str,
    channel_stage: str,
    include_shorts: bool = False,
) -> dict:
    """
    Generate a structured 4-week content calendar scaffold.
    Claude fills in the actual video ideas; this function returns the
    structural template that Claude will populate with its reasoning.
    """
    freq_map = {"1x/week": 1, "2x/week": 2, "3x/week": 3, "daily": 7}
    videos_per_week = freq_map.get(upload_frequency, 1)

    strategy_focus = {
        "new": "discoverability and broad appeal — prioritize searchable tutorial/how-to content",
        "growing": "audience retention and community building — mix tutorials with engaging vlogs",
        "near_monetization": "watch-time maximization — longer deep-dive videos and series",
    }.get(channel_stage, "balanced growth")

    return {
        "calendar_config": {
            "niche": niche,
            "target_audience": target_audience,
            "upload_frequency": upload_frequency,
            "videos_per_week": videos_per_week,
            "include_shorts": include_shorts,
            "channel_stage": channel_stage,
            "strategy_focus": strategy_focus,
            "weeks": 4,
            "total_long_form_slots": videos_per_week * 4,
            "total_shorts_slots": (videos_per_week * 4 * 2) if include_shorts else 0,
        },
        "instruction_for_agent": (
            "Using the config above, generate a detailed 4-week content calendar. "
            "For each video slot provide: title idea, content angle, why it appeals "
            "to the target audience, expected watch-time range, and a one-line hook."
        ),
    }


def optimize_video_metadata(
    video_topic: str,
    niche: str,
    video_type: str,
    target_keywords: list[str] | None = None,
) -> dict:
    """Return a prompt scaffold for Claude to generate SEO-optimized metadata."""
    return {
        "video_topic": video_topic,
        "niche": niche,
        "video_type": video_type,
        "target_keywords": target_keywords or [],
        "metadata_fields_to_generate": [
            "title_options (3 variations: curiosity-driven, keyword-rich, emotional)",
            "description (first 150 chars optimized for search preview, then timestamps, links, CTA)",
            "tags (15-20 relevant tags mixing broad and long-tail)",
            "thumbnail_text_overlay (max 4 words, high contrast)",
            "chapter_titles (if applicable)",
        ],
        "seo_principles": [
            "Include primary keyword in title within first 5 words",
            "Use numbers when possible (e.g., '7 Ways to...')",
            "Create curiosity gap or promise clear value",
            "First 2 sentences of description must include primary + secondary keywords",
        ],
    }


def suggest_viral_hooks(
    video_topic: str,
    niche: str,
    hook_style: str,
    num_hooks: int,
) -> dict:
    """Return a scaffold for Claude to generate hook scripts."""
    style_guidance = {
        "question": "Open with a provocative question the viewer desperately wants answered.",
        "shock": "Lead with a surprising fact, statistic, or counter-intuitive claim.",
        "story": "Begin in the middle of a dramatic moment that relates to the topic.",
        "challenge": "Dare the viewer or set up an impossible-seeming challenge.",
        "controversy": "Take a bold stance that challenges common wisdom in the niche.",
    }

    return {
        "video_topic": video_topic,
        "niche": niche,
        "hook_style": hook_style,
        "style_guidance": style_guidance.get(hook_style, ""),
        "num_hooks_requested": num_hooks,
        "hook_structure": {
            "seconds_0_3": "Pattern interrupt — grab attention immediately",
            "seconds_3_8": "Amplify the problem/promise",
            "seconds_8_15": "Tease the payoff without revealing it",
        },
        "thumbnail_concepts_to_generate": num_hooks,
        "instruction_for_agent": (
            f"Generate {num_hooks} complete hook scripts (0-15 seconds each) "
            f"using the '{hook_style}' style, plus a matching thumbnail concept for each."
        ),
    }


def build_monetization_roadmap(
    channel_name: str,
    niche: str,
    current_subscribers: int,
    current_watch_hours: float,
    weekly_upload_capacity: int,
    content_strengths: list[str] | None = None,
) -> dict:
    """Return a scaffold for Claude to build a personalized monetization roadmap."""
    sub_pct = min(100, round(current_subscribers / 1000 * 100, 1))
    wh_pct = min(100, round(current_watch_hours / 4000 * 100, 1))

    milestones = []
    if current_subscribers < 100:
        milestones.append({"target": "100 subscribers", "focus": "validation & first loyal fans"})
    if current_subscribers < 500:
        milestones.append({"target": "500 subscribers", "focus": "algorithm trust building"})
    if current_subscribers < 1000:
        milestones.append({"target": "1,000 subscribers + 4,000 watch hours", "focus": "YPP eligibility"})
    milestones.append({"target": "Post-monetization", "focus": "revenue diversification"})

    revenue_streams = [
        "YouTube AdSense (requires YPP approval)",
        "Channel Memberships (requires 500 subs + YPP)",
        "Super Thanks / Super Chat (requires YPP)",
        "Affiliate marketing (can start NOW — no YPP needed)",
        "Brand sponsorships (can start at ~1K subs in most niches)",
        "Digital products / courses",
        "Merchandise (Merch Shelf available at 10K subs)",
        "Patreon / Buy Me a Coffee (can start NOW)",
    ]

    return {
        "channel_name": channel_name,
        "niche": niche,
        "current_progress": {
            "subscribers": {"current": current_subscribers, "goal": 1000, "pct": sub_pct},
            "watch_hours": {"current": current_watch_hours, "goal": 4000, "pct": wh_pct},
        },
        "weekly_upload_capacity": weekly_upload_capacity,
        "content_strengths": content_strengths or [],
        "milestone_targets": milestones,
        "available_revenue_streams": revenue_streams,
        "instruction_for_agent": (
            "Using the data above, create a detailed week-by-week action plan "
            "for the next 8 weeks with specific content types, posting schedules, "
            "engagement tactics, and early revenue opportunities the creator can "
            "pursue before reaching YPP thresholds."
        ),
    }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "analyze_monetization_gap": analyze_monetization_gap,
    "generate_content_calendar": generate_content_calendar,
    "optimize_video_metadata": optimize_video_metadata,
    "suggest_viral_hooks": suggest_viral_hooks,
    "build_monetization_roadmap": build_monetization_roadmap,
}


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**tool_input)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})

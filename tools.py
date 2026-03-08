"""
Tool definitions and implementations for the Growther Agent.
Covers YouTube, Instagram, TikTok, Twitter/X, and Facebook.
"""

import json
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Tool definitions (JSON schema for the Anthropic API)
# ---------------------------------------------------------------------------

TOOLS = [
    # ── YouTube ──────────────────────────────────────────────────────────────
    {
        "name": "analyze_monetization_gap",
        "description": (
            "Analyze how far a YouTube channel is from YPP monetization requirements. "
            "Returns gap in subscribers and watch hours, estimated timeline, and "
            "percentage completion for each metric."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "current_subscribers": {"type": "integer", "description": "Current subscriber count."},
                "current_watch_hours": {"type": "number", "description": "Total public watch hours in last 12 months."},
                "weekly_subscriber_growth": {"type": "integer", "description": "Average new subscribers per week."},
                "weekly_watch_hours": {"type": "number", "description": "Average public watch hours per week."},
                "uses_shorts": {"type": "boolean", "description": "Whether the channel uses YouTube Shorts."},
                "current_shorts_views_90d": {"type": "integer", "description": "Shorts views in last 90 days."},
                "weekly_shorts_views": {"type": "integer", "description": "Average Shorts views per week."},
            },
            "required": ["current_subscribers", "current_watch_hours", "weekly_subscriber_growth", "weekly_watch_hours"],
        },
    },
    # ── Instagram ─────────────────────────────────────────────────────────────
    {
        "name": "analyze_instagram_profile",
        "description": (
            "Analyze an Instagram account's current standing toward monetization milestones. "
            "Returns follower gap, engagement rate assessment, growth timeline, and "
            "which monetization features are currently unlocked."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "followers": {"type": "integer", "description": "Current follower count."},
                "following": {"type": "integer", "description": "Number of accounts followed."},
                "total_posts": {"type": "integer", "description": "Total posts published."},
                "avg_likes_per_post": {"type": "number", "description": "Average likes per post."},
                "avg_comments_per_post": {"type": "number", "description": "Average comments per post."},
                "avg_reel_plays": {"type": "number", "description": "Average Reels plays per reel."},
                "posts_per_week": {"type": "number", "description": "Average posts published per week."},
                "weekly_follower_growth": {"type": "integer", "description": "Average new followers per week."},
            },
            "required": ["followers", "avg_likes_per_post", "posts_per_week", "weekly_follower_growth"],
        },
    },
    # ── TikTok ────────────────────────────────────────────────────────────────
    {
        "name": "analyze_tiktok_profile",
        "description": (
            "Analyze a TikTok account's progress toward Creator Fund and other "
            "monetization milestones. Returns follower and view gaps, engagement rate, "
            "and estimated timeline to each monetization threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "followers": {"type": "integer", "description": "Current follower count."},
                "total_likes": {"type": "integer", "description": "Total lifetime likes across all videos."},
                "avg_video_views": {"type": "number", "description": "Average views per video."},
                "videos_last_30d": {"type": "integer", "description": "Number of videos posted in last 30 days."},
                "total_views_last_30d": {"type": "integer", "description": "Total views in last 30 days."},
                "weekly_follower_growth": {"type": "integer", "description": "Average new followers per week."},
                "videos_per_week": {"type": "number", "description": "Average videos posted per week."},
            },
            "required": ["followers", "avg_video_views", "videos_last_30d", "total_views_last_30d", "weekly_follower_growth"],
        },
    },
    # ── Twitter / X ───────────────────────────────────────────────────────────
    {
        "name": "analyze_twitter_profile",
        "description": (
            "Analyze a Twitter/X account's progress toward X Ads Revenue Sharing and "
            "other monetization features. Returns follower and impression gaps, "
            "engagement rate, and estimated timeline."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "followers": {"type": "integer", "description": "Current follower count."},
                "monthly_impressions": {"type": "integer", "description": "Total impressions in last 30 days."},
                "avg_likes_per_tweet": {"type": "number", "description": "Average likes per tweet."},
                "avg_retweets_per_tweet": {"type": "number", "description": "Average retweets per tweet."},
                "tweets_per_week": {"type": "number", "description": "Average tweets posted per week."},
                "weekly_follower_growth": {"type": "integer", "description": "Average new followers per week."},
                "has_x_premium": {"type": "boolean", "description": "Whether the account has X Premium subscription."},
            },
            "required": ["followers", "monthly_impressions", "tweets_per_week", "weekly_follower_growth"],
        },
    },
    # ── Facebook ──────────────────────────────────────────────────────────────
    {
        "name": "analyze_facebook_page",
        "description": (
            "Analyze a Facebook page's progress toward in-stream ads, Stars, and "
            "other monetization features. Returns follower and watch-time gaps and "
            "estimated timeline to each threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_followers": {"type": "integer", "description": "Current page follower/like count."},
                "avg_post_reach": {"type": "integer", "description": "Average organic reach per post."},
                "avg_post_engagement": {"type": "number", "description": "Average engagements per post."},
                "posts_per_week": {"type": "number", "description": "Average posts published per week."},
                "video_minutes_watched_60d": {"type": "integer", "description": "Total video minutes watched in last 60 days."},
                "weekly_follower_growth": {"type": "integer", "description": "Average new followers per week."},
                "active_videos": {"type": "integer", "description": "Number of active videos on the page."},
            },
            "required": ["page_followers", "posts_per_week", "weekly_follower_growth"],
        },
    },
    # ── Cross-platform ────────────────────────────────────────────────────────
    {
        "name": "generate_platform_content_strategy",
        "description": (
            "Generate a platform-specific 4-week content strategy with post ideas, "
            "frequency recommendations, content formats, and growth tactics tailored "
            "to the platform's current algorithm."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["youtube", "instagram", "tiktok", "twitter", "facebook"],
                    "description": "The social media platform.",
                },
                "niche": {"type": "string", "description": "The account's content niche."},
                "target_audience": {"type": "string", "description": "Description of the target audience."},
                "posts_per_week": {"type": "number", "description": "How many posts the creator can publish per week."},
                "channel_stage": {
                    "type": "string",
                    "enum": ["new", "growing", "near_monetization"],
                    "description": "Stage of the account.",
                },
                "content_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Content formats available (e.g. ['short-form video', 'long-form video', 'images', 'carousels']).",
                },
            },
            "required": ["platform", "niche", "target_audience", "posts_per_week", "channel_stage"],
        },
    },
    {
        "name": "generate_content_calendar",
        "description": (
            "Generate a structured 4-week YouTube content calendar with video ideas, "
            "recommended upload days, content types, and strategic notes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "niche": {"type": "string"},
                "target_audience": {"type": "string"},
                "upload_frequency": {
                    "type": "string",
                    "enum": ["1x/week", "2x/week", "3x/week", "daily"],
                },
                "include_shorts": {"type": "boolean"},
                "channel_stage": {
                    "type": "string",
                    "enum": ["new", "growing", "near_monetization"],
                },
            },
            "required": ["niche", "target_audience", "upload_frequency", "channel_stage"],
        },
    },
    {
        "name": "optimize_video_metadata",
        "description": (
            "Generate SEO-optimized title, description, and tag recommendations "
            "for a YouTube video."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_topic": {"type": "string"},
                "niche": {"type": "string"},
                "target_keywords": {"type": "array", "items": {"type": "string"}},
                "video_type": {
                    "type": "string",
                    "enum": ["tutorial", "vlog", "review", "list", "story", "shorts"],
                },
            },
            "required": ["video_topic", "niche", "video_type"],
        },
    },
    {
        "name": "suggest_viral_hooks",
        "description": (
            "Generate compelling hooks (opening scripts) and thumbnail/cover concepts "
            "to maximize retention and click-through rate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_topic": {"type": "string"},
                "niche": {"type": "string"},
                "hook_style": {
                    "type": "string",
                    "enum": ["question", "shock", "story", "challenge", "controversy"],
                },
                "num_hooks": {"type": "integer", "minimum": 1, "maximum": 5},
                "platform": {
                    "type": "string",
                    "enum": ["youtube", "instagram", "tiktok", "twitter", "facebook"],
                    "description": "Platform the hook is for (affects length and style).",
                },
            },
            "required": ["video_topic", "niche", "hook_style", "num_hooks"],
        },
    },
    {
        "name": "build_monetization_roadmap",
        "description": (
            "Build a personalized step-by-step monetization roadmap with milestone "
            "targets, weekly action items, and revenue stream advice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_name": {"type": "string"},
                "niche": {"type": "string"},
                "platform": {
                    "type": "string",
                    "enum": ["youtube", "instagram", "tiktok", "twitter", "facebook"],
                },
                "current_followers": {"type": "integer", "description": "Current follower/subscriber count."},
                "current_watch_hours": {"type": "number", "description": "Watch hours (YouTube) or equivalent engagement metric."},
                "weekly_upload_capacity": {"type": "integer"},
                "content_strengths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["channel_name", "niche", "platform", "current_followers", "weekly_upload_capacity"],
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
    SUB_GOAL, WH_GOAL, SHORTS_GOAL = 1000, 4000, 10_000_000
    sub_gap = max(0, SUB_GOAL - current_subscribers)
    wh_gap = max(0, WH_GOAL - current_watch_hours)

    def weeks(gap, rate): return round(gap / rate, 1) if rate > 0 and gap > 0 else 0
    def eta(w): return (datetime.today() + timedelta(weeks=w)).strftime("%B %d, %Y") if w > 0 else "Already eligible"

    w_subs = weeks(sub_gap, weekly_subscriber_growth)
    w_wh = weeks(wh_gap, weekly_watch_hours)
    w_total = max(w_subs, w_wh)

    result = {
        "long_form_path": {
            "subscribers": {"current": current_subscribers, "goal": SUB_GOAL, "gap": sub_gap,
                            "completion_pct": min(100, round(current_subscribers / SUB_GOAL * 100, 1)),
                            "weeks_to_goal": w_subs},
            "watch_hours_12m": {"current": current_watch_hours, "goal": WH_GOAL, "gap": round(wh_gap, 1),
                                 "completion_pct": min(100, round(current_watch_hours / WH_GOAL * 100, 1)),
                                 "weeks_to_goal": w_wh},
            "bottleneck": "subscribers" if w_subs > w_wh else "watch_hours",
            "estimated_weeks_to_monetize": w_total,
            "estimated_monetization_date": eta(w_total),
        }
    }

    if uses_shorts:
        shorts_gap = max(0, SHORTS_GOAL - current_shorts_views_90d)
        w_shorts = weeks(shorts_gap, weekly_shorts_views)
        result["shorts_path"] = {
            "current_views_90d": current_shorts_views_90d, "goal": SHORTS_GOAL,
            "gap": shorts_gap,
            "completion_pct": min(100, round(current_shorts_views_90d / SHORTS_GOAL * 100, 1)),
            "weeks_to_goal": w_shorts, "estimated_monetization_date": eta(w_shorts),
        }
    return result


def analyze_instagram_profile(
    followers: int,
    avg_likes_per_post: float,
    posts_per_week: float,
    weekly_follower_growth: int,
    following: int = 0,
    total_posts: int = 0,
    avg_comments_per_post: float = 0,
    avg_reel_plays: float = 0,
) -> dict:
    engagement_rate = round((avg_likes_per_post + avg_comments_per_post) / max(followers, 1) * 100, 2)
    health = "Excellent (>6%)" if engagement_rate > 6 else "Good (3-6%)" if engagement_rate > 3 else "Below average (<3%) — focus on engagement"

    milestones = {
        "affiliate_tools": {"threshold": "any", "unlocked": True},
        "badges_in_live": {"threshold": 10000, "unlocked": followers >= 10000,
                           "gap": max(0, 10000 - followers),
                           "weeks_to_unlock": round(max(0, 10000 - followers) / weekly_follower_growth, 1) if weekly_follower_growth > 0 else None},
        "creator_marketplace": {"threshold": 10000, "unlocked": followers >= 10000,
                                "gap": max(0, 10000 - followers)},
        "subscriptions": {"threshold": "varies by region", "unlocked": followers >= 10000},
    }
    return {
        "followers": followers, "engagement_rate_pct": engagement_rate,
        "engagement_health": health, "posts_per_week": posts_per_week,
        "avg_reel_plays": avg_reel_plays, "weekly_follower_growth": weekly_follower_growth,
        "monetization_milestones": milestones,
        "estimated_weeks_to_10k": round((10000 - followers) / weekly_follower_growth, 1) if weekly_follower_growth > 0 and followers < 10000 else 0,
    }


def analyze_tiktok_profile(
    followers: int,
    avg_video_views: float,
    videos_last_30d: int,
    total_views_last_30d: int,
    weekly_follower_growth: int,
    total_likes: int = 0,
    videos_per_week: float = 0,
) -> dict:
    CREATOR_FUND_FOLLOWERS = 10_000
    CREATOR_FUND_VIEWS_30D = 100_000

    follower_gap = max(0, CREATOR_FUND_FOLLOWERS - followers)
    views_gap = max(0, CREATOR_FUND_VIEWS_30D - total_views_last_30d)

    weeks_followers = round(follower_gap / weekly_follower_growth, 1) if weekly_follower_growth > 0 and follower_gap > 0 else 0
    views_per_week = total_views_last_30d / 4 if total_views_last_30d else 0
    weeks_views = round(views_gap / views_per_week, 1) if views_per_week > 0 and views_gap > 0 else 0

    def eta(w): return (datetime.today() + timedelta(weeks=w)).strftime("%B %d, %Y") if w > 0 else "Already eligible"

    return {
        "followers": followers, "avg_video_views": avg_video_views,
        "total_views_last_30d": total_views_last_30d, "videos_last_30d": videos_last_30d,
        "monetization_milestones": {
            "live_gifting_1k": {"threshold": 1000, "unlocked": followers >= 1000,
                                "gap": max(0, 1000 - followers)},
            "creator_fund_10k": {
                "threshold_followers": CREATOR_FUND_FOLLOWERS,
                "threshold_views_30d": CREATOR_FUND_VIEWS_30D,
                "unlocked": followers >= CREATOR_FUND_FOLLOWERS and total_views_last_30d >= CREATOR_FUND_VIEWS_30D,
                "follower_gap": follower_gap, "views_gap": views_gap,
                "bottleneck": "followers" if weeks_followers > weeks_views else "views",
                "estimated_weeks": max(weeks_followers, weeks_views),
                "estimated_date": eta(max(weeks_followers, weeks_views)),
            },
            "series_10k": {"threshold": 10000, "unlocked": followers >= 10000, "gap": max(0, 10000 - followers)},
        },
    }


def analyze_twitter_profile(
    followers: int,
    monthly_impressions: int,
    tweets_per_week: float,
    weekly_follower_growth: int,
    avg_likes_per_tweet: float = 0,
    avg_retweets_per_tweet: float = 0,
    has_x_premium: bool = False,
) -> dict:
    FOLLOWER_GOAL = 500
    IMPRESSIONS_3M_GOAL = 5_000_000

    follower_gap = max(0, FOLLOWER_GOAL - followers)
    impressions_3m = monthly_impressions * 3
    impressions_gap = max(0, IMPRESSIONS_3M_GOAL - impressions_3m)

    weeks_followers = round(follower_gap / weekly_follower_growth, 1) if weekly_follower_growth > 0 and follower_gap > 0 else 0
    weekly_impressions = monthly_impressions / 4
    weeks_impressions = round(impressions_gap / weekly_impressions, 1) if weekly_impressions > 0 and impressions_gap > 0 else 0

    def eta(w): return (datetime.today() + timedelta(weeks=w)).strftime("%B %d, %Y") if w > 0 else "Threshold met"

    engagement_rate = round((avg_likes_per_tweet + avg_retweets_per_tweet) / max(followers / 100, 1), 2)

    return {
        "followers": followers, "monthly_impressions": monthly_impressions,
        "impressions_3m_estimate": impressions_3m, "engagement_rate_pct": engagement_rate,
        "has_x_premium": has_x_premium,
        "ads_revenue_sharing": {
            "requires_x_premium": True, "has_x_premium": has_x_premium,
            "follower_threshold": FOLLOWER_GOAL, "follower_gap": follower_gap,
            "impressions_3m_threshold": IMPRESSIONS_3M_GOAL,
            "impressions_3m_gap": impressions_gap,
            "bottleneck": "followers" if weeks_followers > weeks_impressions else "impressions",
            "estimated_weeks": max(weeks_followers, weeks_impressions),
            "estimated_date": eta(max(weeks_followers, weeks_impressions)),
            "note": "X Premium subscription required for revenue sharing" if not has_x_premium else "",
        },
    }


def analyze_facebook_page(
    page_followers: int,
    posts_per_week: float,
    weekly_follower_growth: int,
    avg_post_reach: int = 0,
    avg_post_engagement: float = 0,
    video_minutes_watched_60d: int = 0,
    active_videos: int = 0,
) -> dict:
    INSTREAMADS_FOLLOWERS = 10_000
    INSTREAMADS_MINUTES = 600_000
    INSTREAMADS_VIDEOS = 5
    STARS_FOLLOWERS = 1_000

    def weeks(gap, rate): return round(gap / rate, 1) if rate > 0 and gap > 0 else 0
    def eta(w): return (datetime.today() + timedelta(weeks=w)).strftime("%B %d, %Y") if w > 0 else "Already eligible"

    follower_gap_instreamads = max(0, INSTREAMADS_FOLLOWERS - page_followers)
    w_followers = weeks(follower_gap_instreamads, weekly_follower_growth)

    weekly_minutes = video_minutes_watched_60d / 8 if video_minutes_watched_60d else 0
    minutes_gap = max(0, INSTREAMADS_MINUTES - video_minutes_watched_60d)
    w_minutes = weeks(minutes_gap, weekly_minutes)

    return {
        "page_followers": page_followers, "posts_per_week": posts_per_week,
        "video_minutes_watched_60d": video_minutes_watched_60d,
        "active_videos": active_videos,
        "engagement_rate_pct": round(avg_post_engagement / max(avg_post_reach, 1) * 100, 2) if avg_post_reach else 0,
        "monetization_milestones": {
            "stars_live": {"threshold": STARS_FOLLOWERS, "unlocked": page_followers >= STARS_FOLLOWERS,
                           "gap": max(0, STARS_FOLLOWERS - page_followers),
                           "weeks_to_unlock": weeks(max(0, STARS_FOLLOWERS - page_followers), weekly_follower_growth)},
            "in_stream_ads": {
                "follower_threshold": INSTREAMADS_FOLLOWERS, "follower_gap": follower_gap_instreamads,
                "minutes_threshold": INSTREAMADS_MINUTES, "minutes_gap": minutes_gap,
                "videos_threshold": INSTREAMADS_VIDEOS, "active_videos": active_videos, "videos_gap": max(0, INSTREAMADS_VIDEOS - active_videos),
                "unlocked": page_followers >= INSTREAMADS_FOLLOWERS and video_minutes_watched_60d >= INSTREAMADS_MINUTES and active_videos >= INSTREAMADS_VIDEOS,
                "bottleneck": "followers" if w_followers > w_minutes else "video_minutes",
                "estimated_weeks": max(w_followers, w_minutes),
                "estimated_date": eta(max(w_followers, w_minutes)),
            },
        },
    }


def generate_platform_content_strategy(
    platform: str,
    niche: str,
    target_audience: str,
    posts_per_week: float,
    channel_stage: str,
    content_formats: list[str] | None = None,
) -> dict:
    strategy_focus = {
        "new": "discoverability and first-impression authority — searchable, evergreen content",
        "growing": "community building and retention — mix of value and personality-driven posts",
        "near_monetization": "watch-time/engagement maximization — longer, deeper content series",
    }.get(channel_stage, "balanced growth")

    platform_tips = {
        "youtube": ["Post on Tue/Wed/Thu for best algorithm lift", "Aim for 8–15 min for ad breaks", "First 48h views are critical — promote immediately after upload"],
        "instagram": ["Reels get 3× more reach than static posts", "Post Reels at 9am–12pm or 7pm–9pm", "Use 3–5 niche hashtags max, not 30 generic ones", "Stories daily = higher feed reach"],
        "tiktok": ["Post 1–3× per day for fastest growth", "First 2 seconds must grab attention — no intros", "Niche-specific sounds boost discoverability", "Respond to comments with video replies"],
        "twitter": ["Tweet 3–5× per day including replies", "Threads get 5× more impressions than single tweets", "Engage with larger accounts in your niche daily", "Tweet within the first 2 hours of trending topics"],
        "facebook": ["Video gets 5× more reach than links", "Facebook Live gets 6× more interactions", "Post natively — avoid external links in main post text", "Groups drive more organic reach than pages"],
    }

    return {
        "platform": platform, "niche": niche, "target_audience": target_audience,
        "posts_per_week": posts_per_week, "channel_stage": channel_stage,
        "strategy_focus": strategy_focus,
        "content_formats": content_formats or [],
        "platform_algorithm_tips": platform_tips.get(platform, []),
        "weeks": 4,
        "total_post_slots": int(posts_per_week * 4),
        "instruction_for_agent": (
            f"Generate a detailed 4-week content calendar for {platform} in the {niche} niche. "
            f"For each post slot include: specific topic/title, content angle, format, "
            f"why it appeals to {target_audience}, and one strong hook line. "
            f"Strategy focus: {strategy_focus}."
        ),
    }


def generate_content_calendar(
    niche: str,
    target_audience: str,
    upload_frequency: str,
    channel_stage: str,
    include_shorts: bool = False,
) -> dict:
    freq_map = {"1x/week": 1, "2x/week": 2, "3x/week": 3, "daily": 7}
    vpw = freq_map.get(upload_frequency, 1)
    strategy_focus = {
        "new": "discoverability — searchable tutorial/how-to content",
        "growing": "retention — mix tutorials with engaging personality content",
        "near_monetization": "watch-time — longer deep-dives and series",
    }.get(channel_stage, "balanced growth")
    return {
        "calendar_config": {"niche": niche, "target_audience": target_audience,
                             "upload_frequency": upload_frequency, "videos_per_week": vpw,
                             "include_shorts": include_shorts, "channel_stage": channel_stage,
                             "strategy_focus": strategy_focus, "weeks": 4,
                             "total_long_form_slots": vpw * 4,
                             "total_shorts_slots": (vpw * 4 * 2) if include_shorts else 0},
        "instruction_for_agent": (
            "Generate a detailed 4-week YouTube content calendar. "
            "For each slot include: title idea, content angle, why it appeals to the audience, "
            "expected watch-time range, and a one-line hook."
        ),
    }


def optimize_video_metadata(
    video_topic: str,
    niche: str,
    video_type: str,
    target_keywords: list[str] | None = None,
) -> dict:
    return {
        "video_topic": video_topic, "niche": niche, "video_type": video_type,
        "target_keywords": target_keywords or [],
        "metadata_fields_to_generate": [
            "title_options (3 variations: curiosity-driven, keyword-rich, emotional)",
            "description (first 150 chars optimized for search preview, then chapters, links, CTA)",
            "tags (15-20 mixing broad and long-tail)", "thumbnail_text_overlay (max 4 words)",
        ],
        "seo_principles": [
            "Include primary keyword in title within first 5 words",
            "Use numbers when possible", "Create curiosity gap or promise clear value",
            "First 2 sentences of description must include primary + secondary keywords",
        ],
    }


def suggest_viral_hooks(
    video_topic: str,
    niche: str,
    hook_style: str,
    num_hooks: int,
    platform: str = "youtube",
) -> dict:
    style_guidance = {
        "question": "Open with a provocative question the viewer desperately wants answered.",
        "shock": "Lead with a surprising fact, statistic, or counter-intuitive claim.",
        "story": "Begin in the middle of a dramatic moment related to the topic.",
        "challenge": "Dare the viewer or set up an impossible-seeming challenge.",
        "controversy": "Take a bold stance that challenges common wisdom in the niche.",
    }
    hook_lengths = {"youtube": "0-15 seconds", "instagram": "0-3 seconds", "tiktok": "0-2 seconds",
                    "twitter": "first line (140 chars)", "facebook": "0-5 seconds"}
    return {
        "video_topic": video_topic, "niche": niche, "hook_style": hook_style,
        "platform": platform, "style_guidance": style_guidance.get(hook_style, ""),
        "hook_length": hook_lengths.get(platform, "0-15 seconds"),
        "num_hooks_requested": num_hooks,
        "instruction_for_agent": (
            f"Generate {num_hooks} complete hook scripts ({hook_lengths.get(platform, '0-15 seconds')} each) "
            f"using the '{hook_style}' style for {platform}, plus a matching thumbnail/cover concept for each."
        ),
    }


def build_monetization_roadmap(
    channel_name: str,
    niche: str,
    platform: str,
    current_followers: int,
    weekly_upload_capacity: int,
    current_watch_hours: float = 0,
    content_strengths: list[str] | None = None,
) -> dict:
    platform_goals = {
        "youtube": {"primary_goal": "1,000 subscribers + 4,000 watch hours", "secondary": "YPP approval"},
        "instagram": {"primary_goal": "10,000 followers", "secondary": "Creator Marketplace access"},
        "tiktok": {"primary_goal": "10,000 followers + 100K views/month", "secondary": "Creator Fund"},
        "twitter": {"primary_goal": "500 followers + 5M impressions/3 months", "secondary": "Ads Revenue Sharing"},
        "facebook": {"primary_goal": "10,000 followers + 600K video minutes/60 days", "secondary": "In-stream Ads"},
    }

    revenue_streams_by_platform = {
        "youtube": ["YouTube AdSense (YPP)", "Channel Memberships", "Super Thanks", "Affiliate links (NOW)", "Brand deals (~1K)", "Digital products (NOW)", "Patreon (NOW)"],
        "instagram": ["Creator Marketplace brand deals (10K)", "Affiliate links (NOW)", "Instagram Subscriptions", "Badges in Live (10K)", "Digital products (NOW)", "Patreon (NOW)"],
        "tiktok": ["Creator Fund (10K)", "LIVE Gifting (1K)", "TikTok Series (10K)", "Affiliate links (NOW)", "Brand deals (10K+)", "Digital products (NOW)"],
        "twitter": ["X Ads Revenue Sharing (500 + 5M impressions)", "X Subscriptions", "Affiliate links (NOW)", "Sponsored tweets (~5K)", "Newsletter/Substack (NOW)"],
        "facebook": ["In-stream Ads (10K)", "Stars in Live (1K)", "Fan Subscriptions (10K)", "Affiliate links (NOW)", "Brand deals", "Digital products (NOW)"],
    }

    goals = platform_goals.get(platform, {"primary_goal": "10K followers", "secondary": "Monetization"})
    return {
        "channel_name": channel_name, "niche": niche, "platform": platform,
        "current_followers": current_followers,
        "primary_monetization_goal": goals["primary_goal"],
        "secondary_goal": goals["secondary"],
        "weekly_upload_capacity": weekly_upload_capacity,
        "content_strengths": content_strengths or [],
        "available_revenue_streams": revenue_streams_by_platform.get(platform, []),
        "instruction_for_agent": (
            "Using the data above, create a detailed week-by-week action plan for the next 8 weeks "
            "with specific content types, posting schedules, engagement tactics, and early revenue "
            "opportunities the creator can pursue right now before reaching official thresholds."
        ),
    }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "analyze_monetization_gap": analyze_monetization_gap,
    "analyze_instagram_profile": analyze_instagram_profile,
    "analyze_tiktok_profile": analyze_tiktok_profile,
    "analyze_twitter_profile": analyze_twitter_profile,
    "analyze_facebook_page": analyze_facebook_page,
    "generate_platform_content_strategy": generate_platform_content_strategy,
    "generate_content_calendar": generate_content_calendar,
    "optimize_video_metadata": optimize_video_metadata,
    "suggest_viral_hooks": suggest_viral_hooks,
    "build_monetization_roadmap": build_monetization_roadmap,
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(fn(**tool_input), indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})

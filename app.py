"""
Growther Agent — Flask Web Application

Run with:
    python app.py
Then open http://localhost:5000 in your browser.
"""

import json
import os
import uuid

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)

from agent import GrowtherAgent

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "growther-agent-dev-secret-change-in-prod")

# ---------------------------------------------------------------------------
# In-memory conversation store  (use Redis / DB in production)
# ---------------------------------------------------------------------------
# Maps session_id -> {"platform": str, "conversation": list, "profile": dict}
sessions: dict[str, dict] = {}

PLATFORMS = {
    "youtube":   {"label": "YouTube",   "color": "#FF0000", "emoji": "▶"},
    "instagram": {"label": "Instagram", "color": "#E1306C", "emoji": "📸"},
    "tiktok":    {"label": "TikTok",    "color": "#69C9D0", "emoji": "♪"},
    "twitter":   {"label": "Twitter / X","color": "#1DA1F2","emoji": "✕"},
    "facebook":  {"label": "Facebook",  "color": "#1877F2", "emoji": "f"},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_session_id() -> str:
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


def get_agent_session(sid: str) -> dict:
    if sid not in sessions:
        sessions[sid] = {"platform": None, "conversation": [], "profile": {}}
    return sessions[sid]


def build_initial_prompt(platform: str, profile: dict) -> str:
    """Build the opening analysis prompt Claude receives automatically on dashboard load."""
    name = profile.get("account_name") or profile.get("channel_name") or "my account"
    niche = profile.get("niche", "general content")
    audience = profile.get("target_audience", f"people interested in {niche}")

    base = f"Please do a complete growth and monetization analysis for **{name}** on **{platform.title()}**.\n\nHere is my account data:\n"

    if platform == "youtube":
        base += f"""
- **Channel name**: {name}
- **Niche**: {niche}
- **Target audience**: {audience}
- **Subscribers**: {int(profile.get('subscribers', 0)):,}
- **Watch hours (last 12 months)**: {float(profile.get('watch_hours', 0)):,.0f}
- **Weekly new subscribers**: {int(profile.get('weekly_sub_growth', 0)):,}
- **Weekly watch hours**: {float(profile.get('weekly_watch_hours', 0)):,.0f}
- **Uploads per week**: {profile.get('uploads_per_week', 1)}
- **Uses Shorts**: {profile.get('uses_shorts', False)}
- **Shorts views (90 days)**: {int(profile.get('shorts_views_90d', 0)):,}
- **Content strengths**: {profile.get('content_strengths', 'not specified')}
"""
    elif platform == "instagram":
        base += f"""
- **Account name**: {name}
- **Niche**: {niche}
- **Followers**: {int(profile.get('followers', 0)):,}
- **Following**: {int(profile.get('following', 0)):,}
- **Total posts**: {profile.get('total_posts', 0)}
- **Avg likes per post**: {profile.get('avg_likes', 0)}
- **Avg comments per post**: {profile.get('avg_comments', 0)}
- **Avg Reels plays**: {profile.get('avg_reel_plays', 0)}
- **Posts per week**: {profile.get('posts_per_week', 1)}
- **Weekly follower growth**: {int(profile.get('weekly_growth', 0)):,}
"""
    elif platform == "tiktok":
        base += f"""
- **Account name**: {name}
- **Niche**: {niche}
- **Followers**: {int(profile.get('followers', 0)):,}
- **Total likes**: {int(profile.get('total_likes', 0)):,}
- **Avg video views**: {int(profile.get('avg_views', 0)):,}
- **Videos posted last 30 days**: {profile.get('videos_last_30d', 0)}
- **Total views last 30 days**: {int(profile.get('views_last_30d', 0)):,}
- **Videos per week**: {profile.get('videos_per_week', 1)}
- **Weekly follower growth**: {int(profile.get('weekly_growth', 0)):,}
"""
    elif platform == "twitter":
        base += f"""
- **Account name**: {name}
- **Niche**: {niche}
- **Followers**: {int(profile.get('followers', 0)):,}
- **Monthly impressions**: {int(profile.get('monthly_impressions', 0)):,}
- **Avg likes per tweet**: {profile.get('avg_likes', 0)}
- **Avg retweets per tweet**: {profile.get('avg_retweets', 0)}
- **Tweets per week**: {profile.get('tweets_per_week', 0)}
- **Weekly follower growth**: {int(profile.get('weekly_growth', 0)):,}
- **Has X Premium**: {profile.get('has_x_premium', False)}
"""
    elif platform == "facebook":
        base += f"""
- **Page name**: {name}
- **Niche**: {niche}
- **Page followers**: {int(profile.get('page_followers', 0)):,}
- **Avg post reach**: {int(profile.get('avg_reach', 0)):,}
- **Avg post engagements**: {profile.get('avg_engagement', 0)}
- **Posts per week**: {profile.get('posts_per_week', 1)}
- **Video minutes watched (60 days)**: {int(profile.get('video_minutes_60d', 0)):,}
- **Active videos**: {profile.get('active_videos', 0)}
- **Weekly follower growth**: {int(profile.get('weekly_growth', 0)):,}
"""

    base += f"""
Please:
1. Analyze my exact gap to monetization on {platform.title()} with a timeline.
2. Build me a personalized 8-week growth roadmap.
3. Generate a 4-week content calendar with specific post/video ideas for my niche.
4. Recommend the best content formats and hooks to grow faster on {platform.title()}.
5. List any revenue opportunities I can start right now, even before hitting official monetization thresholds.
"""
    return base


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", platforms=PLATFORMS)


@app.route("/connect/<platform>")
def connect(platform: str):
    if platform not in PLATFORMS:
        return redirect(url_for("index"))
    return render_template("connect.html", platform=platform, info=PLATFORMS[platform])


@app.route("/save-profile", methods=["POST"])
def save_profile():
    data = request.get_json()
    platform = data.get("platform")
    profile = data.get("profile", {})

    if not platform or platform not in PLATFORMS:
        return jsonify({"error": "Invalid platform"}), 400

    sid = get_session_id()
    agent_session = get_agent_session(sid)
    agent_session["platform"] = platform
    agent_session["profile"] = profile
    agent_session["conversation"] = []  # fresh conversation for new connection

    return jsonify({"status": "ok", "redirect": url_for("dashboard")})


@app.route("/dashboard")
def dashboard():
    sid = get_session_id()
    agent_session = get_agent_session(sid)

    platform = agent_session.get("platform")
    if not platform:
        return redirect(url_for("index"))

    profile = agent_session.get("profile", {})
    info = PLATFORMS[platform]
    account_name = profile.get("account_name") or profile.get("channel_name") or "Your Account"

    return render_template(
        "dashboard.html",
        platform=platform,
        info=info,
        profile=profile,
        account_name=account_name,
    )


@app.route("/chat/init", methods=["POST"])
def chat_init():
    """Auto-trigger the first analysis when the dashboard loads."""
    sid = get_session_id()
    agent_session = get_agent_session(sid)
    platform = agent_session.get("platform")
    profile = agent_session.get("profile", {})

    if not platform:
        return jsonify({"error": "No platform connected"}), 400

    prompt = build_initial_prompt(platform, profile)

    def generate():
        agent = GrowtherAgent(conversation=agent_session["conversation"])
        agent.set_platform(platform)

        for chunk in agent.chat(prompt):
            # Filter out tool notices (internal) — send all text to client
            payload = json.dumps({"chunk": chunk})
            yield f"data: {payload}\n\n"

        # Persist updated conversation
        agent_session["conversation"] = agent.get_conversation()
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/chat/message", methods=["POST"])
def chat_message():
    """Handle follow-up messages from the user."""
    data = request.get_json()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    sid = get_session_id()
    agent_session = get_agent_session(sid)
    platform = agent_session.get("platform")

    if not platform:
        return jsonify({"error": "No platform connected"}), 400

    def generate():
        agent = GrowtherAgent(conversation=agent_session["conversation"])
        agent.set_platform(platform)

        for chunk in agent.chat(message):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        agent_session["conversation"] = agent.get_conversation()
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/disconnect", methods=["POST"])
def disconnect():
    sid = get_session_id()
    if sid in sessions:
        del sessions[sid]
    session.clear()
    return jsonify({"redirect": url_for("index")})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY is not set.")
        print("   Copy .env.example to .env and add your key.\n")

    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Growther Agent running at http://localhost:{port}\n")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)

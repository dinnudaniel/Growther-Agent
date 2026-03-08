# Growther Agent

An AI-powered YouTube monetization coach that helps creators reach the **YouTube Partner Program (YPP)** thresholds and build a sustainable channel business.

Powered by **Claude Opus 4.6** with adaptive thinking and tool use.

---

## What It Does

The Growther Agent analyzes your YouTube channel and produces:

| Feature | Description |
|---|---|
| **Monetization Gap Analysis** | Exact subscriber/watch-hour gap to YPP with estimated timeline |
| **8-Week Roadmap** | Personalized week-by-week action plan with specific tasks |
| **4-Week Content Calendar** | Specific video ideas, upload schedule, and content strategy |
| **SEO Optimization** | Title variations, description template, and tag strategy |
| **Viral Hook Scripts** | 0–15 second opening scripts + thumbnail concept ideas |
| **Revenue Diversification** | Early revenue streams available before YPP (affiliate, Patreon, etc.) |

---

## YouTube Partner Program Requirements

| Path | Subscribers | Watch Metric |
|---|---|---|
| Long-form | 1,000 | 4,000 watch hours (last 12 months) |
| Shorts | 1,000 | 10,000,000 Shorts views (last 90 days) |

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd Growther-Agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run
python main.py
```

---

## Usage

### Interactive Chat Mode (default)

```bash
python main.py
```

Ask anything about YouTube growth:
- *"How do I get from 300 to 1000 subscribers in 3 months?"*
- *"What type of videos get the most watch time in the cooking niche?"*
- *"Write me a viral hook for a video about budget meal prep"*

### Guided Channel Analysis

```bash
python main.py --analyze
```

Step-by-step prompts collect your channel data, then Claude produces a complete monetization plan.

### Demo Mode

```bash
python main.py --demo
```

Runs a full analysis for a fictional tech channel so you can see the output format.

---

## Project Structure

```
Growther-Agent/
├── main.py          # CLI entry point (interactive, guided, demo modes)
├── agent.py         # Core GrowtherAgent class — agentic loop with Claude Opus 4.6
├── tools.py         # Tool definitions + implementations for Claude to call
├── requirements.txt # Python dependencies
└── .env.example     # Environment variable template
```

### How It Works

1. **User describes their channel** via chat or guided prompts
2. **Claude Opus 4.6** reasons with adaptive thinking about the best strategy
3. **Claude calls tools** (`analyze_monetization_gap`, `generate_content_calendar`, etc.) to get structured data
4. **Tools run locally** and return structured JSON results to Claude
5. **Claude synthesizes** the data into a detailed, personalized response
6. The **agentic loop** continues until Claude has answered everything

---

## Tools Available to Claude

| Tool | Purpose |
|---|---|
| `analyze_monetization_gap` | Calculates exact gap + timeline to YPP for both paths |
| `generate_content_calendar` | Scaffolds a 4-week upload plan |
| `optimize_video_metadata` | SEO title, description, tags scaffold |
| `suggest_viral_hooks` | Hook scripts + thumbnail concepts |
| `build_monetization_roadmap` | 8-week step-by-step action plan |

---

## Requirements

- Python 3.10+
- `anthropic` SDK ≥ 0.40.0
- Valid `ANTHROPIC_API_KEY`

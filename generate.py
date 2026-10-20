from pathlib import Path
from datetime import datetime, timedelta, timezone, date
import json
import math
import os
import random
import textwrap
import urllib.request

USERNAME = "habeeboyediran"
NAME = "Habeeb Oyediran"
ROLE = "Data Scientist + Data Analyst"
STATUS = "Building data-driven and AI-powered solutions"
HEADLINE = "Data Scientist | Data Analyst | AI Product Builder"
BIO = "I help businesses turn data into clear insights, better decisions, and AI-powered data products."

FOCUS = ["Python", "SQL", "Machine Learning", "BI", "AI"]
TOOLS = ["Power BI", "Tableau", "Excel", "Jupyter", "Google Colab", "Git", "GitHub"]
DATA_STACK = ["Pandas", "NumPy", "Scikit-learn", "PostgreSQL"]
AI_SKILLS = ["Prompt Engineering"]

PROJECTS = [
    (
        "Preventive Healthcare Risk Prediction",
        "ML and Power BI project comparing diabetes risk prediction across PIMA and NHANES."
    ),
    (
        "Power BI Data Professional Trends",
        "Power BI analysis exploring trends and insights among data professionals."
    ),
    (
        "Stroke Prediction Analysis",
        "Machine learning project covering preprocessing, EDA and stroke risk classification."
    ),
    (
        "Borkum Tourism Analysis",
        "Python and R analysis of tourism sustainability attitudes and behaviours."
    ),
    (
        "WhatsApp NLP Chat Analysis",
        "NLP project exploring patterns and insights from WhatsApp chat data."
    ),
]

CONTACT = {
    "LinkedIn": "linkedin.com/in/habeeb-oyediran"
}

LINKS = [
    ("LinkedIn", "https://www.linkedin.com/in/habeeb-oyediran"),
    ("Repositories", f"https://github.com/{USERNAME}?tab=repositories"),
]

CARD_WIDTH = 1200
CARD_HEIGHT = 760

LIGHT = {
    "bg": "#f6f8fa",
    "window": "#ffffff",
    "window_stroke": "#d0d7de",
    "panel": "#f6f8fa",
    "panel_stroke": "#d0d7de",
    "text": "#24292f",
    "muted": "#57606a",
    "accent": "#0969da",
    "accent_soft": "#ddf4ff",
    "pill_fill": "#eef6ff",
    "pill_stroke": "#b6e3ff",
    "tile_fill": "#ffffff",
    "tile_stroke": "#d0d7de",
    "dot": "#1f2328",
    "cursor": "#0969da",
    "shadow": "rgba(31,35,40,0.08)",
}

DARK = {
    "bg": "#0d1117",
    "window": "#161b22",
    "window_stroke": "#30363d",
    "panel": "#0d1117",
    "panel_stroke": "#30363d",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#58a6ff",
    "accent_soft": "#1f2a37",
    "pill_fill": "#1b2735",
    "pill_stroke": "#30363d",
    "tile_fill": "#0d1117",
    "tile_stroke": "#30363d",
    "dot": "#f0f6fc",
    "cursor": "#58a6ff",
    "shadow": "rgba(1,4,9,0.45)",
}

ROOT = Path(".")
DOTS_PATH = ROOT / "dots.json"
LIGHT_PATH = ROOT / "light.svg"
DARK_PATH = ROOT / "dark.svg"
SNAKE_PATH = ROOT / "snake.svg"
README_PATH = ROOT / "README.md"

def esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def github_graphql(query: str, variables: dict, token: str) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USERNAME,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
    if "errors" in data:
        raise RuntimeError(f"GitHub API failed: {data['errors']}")
    return data["data"]

def fetch_github_data() -> dict:
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GH_TOKEN is missing. Run with GH_TOKEN=\"$(gh auth token)\" python generate.py")

    now = datetime.now(timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    snake_start = now - timedelta(days=371)

    query = """
    query($login: String!, $yearFrom: DateTime!, $snakeFrom: DateTime!, $to: DateTime!) {
      user(login: $login) {
        login
        name
        repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
          totalCount
          nodes {
            stargazerCount
          }
        }
        yearContributions: contributionsCollection(from: $yearFrom, to: $to) {
          contributionCalendar {
            totalContributions
          }
        }
        snakeContributions: contributionsCollection(from: $snakeFrom, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
                color
                weekday
              }
            }
          }
        }
      }
    }
    """

    data = github_graphql(
        query,
        {
            "login": USERNAME,
            "yearFrom": year_start.isoformat(),
            "snakeFrom": snake_start.isoformat(),
            "to": now.isoformat(),
        },
        token,
    )

    user = data["user"]
    repos = user["repositories"]["nodes"]
    total_stars = sum(node["stargazerCount"] for node in repos)
    public_repos = user["repositories"]["totalCount"]
    contributions_this_year = user["yearContributions"]["contributionCalendar"]["totalContributions"]
    weeks = user["snakeContributions"]["contributionCalendar"]["weeks"]

    days = []
    for week in weeks:
        for d in week["contributionDays"]:
            days.append({
                "date": d["date"],
                "count": d["contributionCount"],
                "weekday": d["weekday"],
                "color": d["color"],
            })

    days.sort(key=lambda x: x["date"])

    current_streak = compute_latest_streak(days)

    return {
        "public_repos": public_repos,
        "total_stars": total_stars,
        "contributions_this_year": contributions_this_year,
        "current_streak": current_streak,
        "weeks": weeks,
        "days": days,
    }

def compute_latest_streak(days: list[dict]) -> int:
    positive_days = [d for d in days if d["count"] > 0]
    if not positive_days:
        return 0

    latest = date.fromisoformat(positive_days[-1]["date"])
    streak = 0
    target = latest
    counts = {date.fromisoformat(d["date"]): d["count"] for d in days}

    while counts.get(target, 0) > 0:
        streak += 1
        target = target - timedelta(days=1)

    return streak

def read_dots() -> list[dict]:
    if not DOTS_PATH.exists():
        raise FileNotFoundError("dots.json is missing. Run portrait.py first.")
    data = json.loads(DOTS_PATH.read_text(encoding="utf-8"))
    return data["points"]

def section_title(title: str, x: int, y: int, delay: float, theme: dict) -> str:
    return f'''
    <text x="{x}" y="{y}" class="section-title fade" style="--delay:{delay:.2f}s; fill:{theme["accent"]};">{esc(title)}</text>
    '''

def text_row(label: str, value: str, x: int, y: int, delay: float, theme: dict) -> str:
    left = f"{label.lower():<14}".replace(" ", ".")
    return f'''
    <text x="{x}" y="{y}" class="row-text fade" style="--delay:{delay:.2f}s; fill:{theme["text"]};">
      <tspan class="label">{esc(left)}</tspan>
      <tspan dx="10">{esc(value)}</tspan>
    </text>
    '''

def pill_svg(label: str, x: float, y: float, delay: float, theme: dict) -> tuple[str, float]:
    char_w = 7.0
    width = max(62.0, 20 + len(label) * char_w)
    svg = f'''
    <g class="fade" style="--delay:{delay:.2f}s;">
      <rect x="{x:.1f}" y="{y:.1f}" rx="14" ry="14" width="{width:.1f}" height="28"
            fill="{theme["pill_fill"]}" stroke="{theme["pill_stroke"]}"/>
      <text x="{x + width/2:.1f}" y="{y + 18:.1f}" text-anchor="middle" class="pill-text"
            fill="{theme["text"]}">{esc(label)}</text>
    </g>
    '''
    return svg, width

def pills_block(title: str, labels: list[str], x: int, y: int, max_width: int, delay: float, theme: dict) -> tuple[str, int, float]:
    svg = [section_title(title, x, y, delay, theme)]
    cur_x = x
    cur_y = y + 16
    delay += 0.05
    line_height = 36

    for label in labels:
        _, width = pill_svg(label, 0, 0, 0, theme)
        if cur_x + width > x + max_width:
            cur_x = x
            cur_y += line_height
        pill, actual_width = pill_svg(label, cur_x, cur_y, delay, theme)
        svg.append(pill)
        cur_x += actual_width + 10
        delay += 0.04

    return "".join(svg), cur_y + 40, delay

def projects_block(x: int, y: int, width: int, delay: float, theme: dict) -> tuple[str, int, float]:
    svg = [section_title("PROJECTS", x, y, delay, theme)]
    delay += 0.05
    cur_y = y + 18

    for title, desc in PROJECTS:
        svg.append(f'''
        <text x="{x}" y="{cur_y}" class="project-title fade" style="--delay:{delay:.2f}s; fill:{theme["text"]};">› {esc(title)}</text>
        ''')
        delay += 0.05
        cur_y += 18

        wrapped = textwrap.wrap(desc, width=52)
        for line in wrapped:
            svg.append(f'''
            <text x="{x + 16}" y="{cur_y}" class="project-desc fade" style="--delay:{delay:.2f}s; fill:{theme["muted"]};">{esc(line)}</text>
            ''')
            delay += 0.04
            cur_y += 16

        cur_y += 10

    return "".join(svg), cur_y, delay

def contact_block(x: int, y: int, delay: float, theme: dict) -> tuple[str, int, float]:
    svg = [section_title("CONTACT", x, y, delay, theme)]
    delay += 0.05
    cur_y = y + 20

    for key, value in CONTACT.items():
        svg.append(f'''
        <text x="{x}" y="{cur_y}" class="project-desc fade" style="--delay:{delay:.2f}s; fill:{theme["text"]};">{esc(key)}  {esc(value)}</text>
        ''')
        delay += 0.05
        cur_y += 18

    return "".join(svg), cur_y, delay

def stat_tile(x: int, y: int, title: str, value: str, delay: float, theme: dict) -> str:
    return f'''
    <g class="fade" style="--delay:{delay:.2f}s;">
      <rect x="{x}" y="{y}" rx="14" ry="14" width="148" height="72"
            fill="{theme["tile_fill"]}" stroke="{theme["tile_stroke"]}"/>
      <text x="{x + 14}" y="{y + 24}" class="tile-label" fill="{theme["muted"]}">{esc(title)}</text>
      <text x="{x + 14}" y="{y + 52}" class="tile-value" fill="{theme["text"]}">{esc(value)}</text>
    </g>
    '''

def build_portrait(points: list[dict], x: int, y: int, size: int, theme: dict) -> str:
    svg = []
    rng = random.Random(42)

    for idx, point in enumerate(points):
        gx = x + point["x"] * size
        gy = y + point["y"] * size
        angle = rng.random() * math.tau
        radius = 140 + rng.random() * 120
        sx = math.cos(angle) * radius
        sy = math.sin(angle) * radius
        r = 0.55 + point["w"] * 1.6
        delay = (idx % 100) * 0.01
        svg.append(
            f'<circle cx="{gx:.2f}" cy="{gy:.2f}" r="{r:.2f}" fill="{theme["dot"]}" '
            f'class="portrait-dot" style="--sx:{sx:.2f}px; --sy:{sy:.2f}px; --delay:{delay:.2f}s;" />'
        )

    return "\n".join(svg)

def build_card(theme: dict, stats: dict, points: list[dict]) -> str:
    left_x = 46
    left_y = 106
    left_w = 360
    left_h = 608

    right_x = 442
    right_y = 116
    right_w = 710

    portrait_x = 86
    portrait_y = 168
    portrait_size = 280

    css = f"""
    <style>
      .root {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
      .fade {{
        opacity: 0;
        animation: fadeUp 0.7s ease forwards;
        animation-delay: var(--delay, 0s);
      }}
      .section-title {{ font-size: 14px; font-weight: 700; letter-spacing: 1.3px; }}
      .row-text {{ font-size: 16px; }}
      .label {{ fill: {theme["muted"]}; }}
      .pill-text {{ font-size: 12px; font-weight: 600; }}
      .project-title {{ font-size: 14px; font-weight: 700; }}
      .project-desc {{ font-size: 13px; }}
      .tile-label {{ font-size: 12px; letter-spacing: 0.4px; }}
      .tile-value {{ font-size: 24px; font-weight: 700; }}
      .small {{ font-size: 13px; fill: {theme["muted"]}; }}
      .main-title {{ font-size: 16px; fill: {theme["text"]}; font-weight: 600; }}
      .headline {{ font-size: 15px; fill: {theme["muted"]}; }}
      .cursor {{
        animation: blink 1s step-end infinite;
      }}
      .portrait-dot {{
        transform-box: fill-box;
        transform-origin: center;
        transform: translate(var(--sx), var(--sy));
        opacity: 0.06;
        animation: gatherScatter 9s ease-in-out infinite;
        animation-delay: var(--delay, 0s);
      }}
      @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes blink {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      @keyframes gatherScatter {{
        0%, 22% {{
          transform: translate(var(--sx), var(--sy));
          opacity: 0.05;
        }}
        34%, 66% {{
          transform: translate(0px, 0px);
          opacity: 0.96;
        }}
        78%, 100% {{
          transform: translate(var(--sx), var(--sy));
          opacity: 0.08;
        }}
      }}
    </style>
    """

    content = []

    content.append(f'''
    <rect x="16" y="16" width="{CARD_WIDTH - 32}" height="{CARD_HEIGHT - 32}" rx="24" ry="24"
          fill="{theme["window"]}" stroke="{theme["window_stroke"]}" />
    ''')
    content.append(f'''
    <rect x="16" y="16" width="{CARD_WIDTH - 32}" height="54" rx="24" ry="24"
          fill="{theme["panel"]}" stroke="{theme["window_stroke"]}" />
    <rect x="16" y="46" width="{CARD_WIDTH - 32}" height="24" fill="{theme["panel"]}" />
    ''')
    content.append(f'''
    <circle cx="42" cy="43" r="7" fill="#ff5f57" />
    <circle cx="66" cy="43" r="7" fill="#febc2e" />
    <circle cx="90" cy="43" r="7" fill="#28c840" />
    ''')
    content.append(f'''
    <text x="122" y="48" class="main-title">{esc(USERNAME)}@github:~$ whoami</text>
    <text x="122" y="98" class="headline fade" style="--delay:0.10s;">{esc(HEADLINE)}</text>
    <text x="122" y="122" class="small fade" style="--delay:0.16s;">{esc(BIO)}</text>
    ''')

    content.append(f'''
    <rect x="{left_x}" y="{left_y}" width="{left_w}" height="{left_h}" rx="20" ry="20"
          fill="{theme["panel"]}" stroke="{theme["panel_stroke"]}" />
    <text x="{left_x + 18}" y="{left_y + 28}" class="section-title fade" style="--delay:0.20s; fill:{theme["accent"]};">VISUAL.MAP</text>
    <rect x="{portrait_x - 16}" y="{portrait_y - 16}" width="{portrait_size + 32}" height="{portrait_size + 32}"
          rx="18" ry="18" fill="{theme["tile_fill"]}" stroke="{theme["panel_stroke"]}" class="fade" style="--delay:0.26s;" />
    ''')
    content.append(build_portrait(points, portrait_x, portrait_y, portrait_size, theme))

    stats_y = portrait_y + portrait_size + 44
    content.append(stat_tile(72, stats_y, "Contributions (YTD)", str(stats["contributions_this_year"]), 0.42, theme))
    content.append(stat_tile(228, stats_y, "Latest Streak", f'{stats["current_streak"]} days', 0.47, theme))
    content.append(stat_tile(72, stats_y + 88, "Public Repos", str(stats["public_repos"]), 0.52, theme))
    content.append(stat_tile(228, stats_y + 88, "Stars", str(stats["total_stars"]), 0.57, theme))

    delay = 0.24
    y = right_y

    content.append(section_title("ROLE", right_x, y, delay, theme))
    delay += 0.05
    y += 22
    content.append(text_row("Role", ROLE, right_x, y, delay, theme))
    delay += 0.05
    y += 28
    content.append(text_row("Status", STATUS, right_x, y, delay, theme))
    delay += 0.05
    y += 36

    block, y, delay = pills_block("FOCUS", FOCUS, right_x, y, right_w, delay, theme)
    content.append(block)

    block, y, delay = pills_block("TOOLS", TOOLS, right_x, y, right_w, delay, theme)
    content.append(block)

    block, y, delay = pills_block("DATA STACK", DATA_STACK, right_x, y, right_w, delay, theme)
    content.append(block)

    block, y, delay = pills_block("AI", AI_SKILLS, right_x, y, right_w, delay, theme)
    content.append(block)

    block, y, delay = projects_block(right_x, y, right_w, delay, theme)
    content.append(block)

    block, y, delay = contact_block(right_x, y, delay, theme)
    content.append(block)

    content.append(f'''
    <text x="52" y="{CARD_HEIGHT - 42}" class="small">{esc(USERNAME)}@github:~$ <tspan class="cursor" fill="{theme["cursor"]}">█</tspan></text>
    ''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" class="root" role="img" aria-label="{esc(NAME)} GitHub profile card">
    {css}
    <rect width="100%" height="100%" fill="{theme["bg"]}" />
    {''.join(content)}
    </svg>'''
    return svg

def contribution_fill(count: int) -> str:
    if count <= 0:
        return "#ebedf0"
    if count < 2:
        return "#9be9a8"
    if count < 5:
        return "#40c463"
    if count < 10:
        return "#30a14e"
    return "#216e39"

def build_snake_svg(weeks: list[dict]) -> str:
    cell = 12
    gap = 4
    margin_x = 26
    margin_y = 38
    cols = len(weeks)
    rows = 7

    width = margin_x * 2 + cols * (cell + gap) - gap
    height = margin_y * 2 + rows * (cell + gap) - gap + 42

    rects = []
    points = []
    overlays = []
    labels = ["Mon", "Wed", "Fri"]

    for week_index, week in enumerate(weeks):
        days = week["contributionDays"]
        for d in days:
            x = margin_x + week_index * (cell + gap)
            y = margin_y + d["weekday"] * (cell + gap)
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" ry="3" fill="{contribution_fill(d["contributionCount"])}" />'
            )
            points.append((x + cell / 2, y + cell / 2))
            if (week_index + d["weekday"]) % 9 == 0:
                delay = ((week_index * 7 + d["weekday"]) % 18) * 0.35
                overlays.append(f'''
                <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" ry="3" fill="#0f172a" opacity="0">
                  <animate attributeName="opacity" values="0;0.55;0" dur="6s" begin="{delay:.2f}s" repeatCount="indefinite" />
                </rect>
                ''')

    serpentine = []
    for col in range(cols):
        week = weeks[col]["contributionDays"]
        ordered = week if col % 2 == 0 else list(reversed(week))
        for d in ordered:
            x = margin_x + col * (cell + gap) + cell / 2
            y = margin_y + d["weekday"] * (cell + gap) + cell / 2
            serpentine.append((x, y))

    path_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in serpentine)

    month_labels = []
    month_seen = set()
    for week_index, week in enumerate(weeks):
        first_day = date.fromisoformat(week["contributionDays"][0]["date"])
        month_key = (first_day.year, first_day.month)
        if month_key not in month_seen:
            month_seen.add(month_key)
            month_labels.append(
                f'<text x="{margin_x + week_index * (cell + gap)}" y="20" font-size="10" fill="#6e7781">{first_day.strftime("%b")}</text>'
            )

    weekday_labels = []
    for weekday, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = margin_y + weekday * (cell + gap) + 9
        weekday_labels.append(f'<text x="0" y="{y}" font-size="10" fill="#6e7781">{label}</text>')

    snake = f'''
    <path id="snake-path" d="{path_d}" fill="none" stroke="none"/>
    <g opacity="0.95">
      <circle r="6" fill="#2ea043">
        <animateMotion dur="18s" repeatCount="indefinite" rotate="auto">
          <mpath href="#snake-path" />
        </animateMotion>
      </circle>
      <circle r="5" fill="#3fb950" opacity="0.85">
        <animateMotion dur="18s" begin="-0.35s" repeatCount="indefinite" rotate="auto">
          <mpath href="#snake-path" />
        </animateMotion>
      </circle>
      <circle r="4.5" fill="#56d364" opacity="0.72">
        <animateMotion dur="18s" begin="-0.70s" repeatCount="indefinite" rotate="auto">
          <mpath href="#snake-path" />
        </animateMotion>
      </circle>
      <circle r="4" fill="#7ee787" opacity="0.60">
        <animateMotion dur="18s" begin="-1.05s" repeatCount="indefinite" rotate="auto">
          <mpath href="#snake-path" />
        </animateMotion>
      </circle>
      <circle r="3.5" fill="#a5f3ad" opacity="0.48">
        <animateMotion dur="18s" begin="-1.40s" repeatCount="indefinite" rotate="auto">
          <mpath href="#snake-path" />
        </animateMotion>
      </circle>
    </g>
    '''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution snake">
    <style>
      text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    </style>
    <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" ry="14" fill="transparent" stroke="#d0d7de"/>
    <text x="16" y="{height - 16}" font-size="11" fill="#6e7781">{esc(USERNAME)} contributions · last 12 months</text>
    {''.join(month_labels)}
    {''.join(weekday_labels)}
    {''.join(rects)}
    {''.join(overlays)}
    {snake}
    </svg>'''
    return svg

def build_readme() -> str:
    links_row = " • ".join(
        f'<a href="{url}">{esc(label)}</a>' for label, url in LINKS
    )

    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="light.svg">
  <img alt="{esc(NAME)} terminal-style GitHub profile card" src="light.svg" width="100%">
</picture>

<p align="center">
  {links_row}
</p>

<img alt="{esc(NAME)} contribution snake" src="snake.svg" width="100%">
'''

def main():
    stats = fetch_github_data()
    points = read_dots()

    light_svg = build_card(LIGHT, stats, points)
    dark_svg = build_card(DARK, stats, points)
    snake_svg = build_snake_svg(stats["weeks"])
    readme = build_readme()

    LIGHT_PATH.write_text(light_svg, encoding="utf-8")
    DARK_PATH.write_text(dark_svg, encoding="utf-8")
    SNAKE_PATH.write_text(snake_svg, encoding="utf-8")
    README_PATH.write_text(readme, encoding="utf-8")

    print("Generated:")
    print(" - light.svg")
    print(" - dark.svg")
    print(" - snake.svg")
    print(" - README.md")

if __name__ == "__main__":
    main()

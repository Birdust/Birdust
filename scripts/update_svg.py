"""neofetch 스타일 프로필 카드(dark_mode.svg / light_mode.svg)를 생성한다.

GitHub Actions에서 매일 실행되어 Uptime과 GitHub Stats를 갱신한다.
표준 라이브러리만 사용한다.

    GITHUB_TOKEN=... python scripts/update_svg.py
"""

import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

LOGIN = "Birdust"
BIRTHDAY = date(2001, 9, 22)
KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]

# 오른쪽 정보 영역 폭(글자 수). 점선으로 값 끝을 이 폭에 맞춘다.
COLS = 64
CHAR_W = 9.7  # 16px 고정폭 폰트 한 글자 폭(넉넉하게 잡은 값)
LINE_H = 20
ART_X = 15
INFO_X = 400

CAT = r"""
  ____________________________
 < thanks for stopping by! :D >
  ----------------------------
          \
           \
            /\_/\
           ( o.o )
           =\ ^ /=
          /       \
         /  |   |  \
        (   |   |   )
         \__|___|__/
            _| |_
""".strip("\n").splitlines()

THEMES = {
    "dark": {
        "bg": "#161b22",
        "text": "#c9d1d9",
        "key": "#ffa657",
        "value": "#a5d6ff",
        "dots": "#616e7f",
        "art": "#c9d1d9",
    },
    "light": {
        "bg": "#f6f8fa",
        "text": "#24292f",
        "key": "#953800",
        "value": "#0a3069",
        "dots": "#c2cfde",
        "art": "#24292f",
    },
}


def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as res:
        body = json.load(res)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch_stats():
    # 로컬 토큰이든 Actions 토큰이든 같은 숫자가 나오도록 공개 데이터만 센다.
    repos, stars, cursor = 0, 0, None
    while True:
        data = graphql(
            """
            query($login: String!, $cursor: String) {
              user(login: $login) {
                repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, after: $cursor) {
                  totalCount
                  nodes { stargazerCount }
                  pageInfo { hasNextPage endCursor }
                }
              }
            }
            """,
            {"login": LOGIN, "cursor": cursor},
        )["user"]["repositories"]
        repos = data["totalCount"]
        stars += sum(n["stargazerCount"] for n in data["nodes"])
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]

    user = graphql(
        """
        query($login: String!) {
          user(login: $login) {
            createdAt
            followers { totalCount }
            repositoriesContributedTo(
              privacy: PUBLIC
              contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]
            ) { totalCount }
          }
        }
        """,
        {"login": LOGIN},
    )["user"]

    # contributionsCollection은 1년 단위로만 조회돼서 가입 연도부터 연도별로 합산한다.
    commits = 0
    now = datetime.now(timezone.utc)
    for year in range(int(user["createdAt"][:4]), now.year + 1):
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = min(datetime(year + 1, 1, 1, tzinfo=timezone.utc), now)
        commits += graphql(
            """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) { totalCommitContributions }
              }
            }
            """,
            {"login": LOGIN, "from": start.isoformat(), "to": end.isoformat()},
        )["user"]["contributionsCollection"]["totalCommitContributions"]

    return {
        "repos": repos,
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "stars": stars,
        "commits": commits,
        "followers": user["followers"]["totalCount"],
    }


def uptime(today):
    years = today.year - BIRTHDAY.year
    months = today.month - BIRTHDAY.month
    days = today.day - BIRTHDAY.day
    if days < 0:
        months -= 1
        prev_month_end = today.replace(day=1) - timedelta(days=1)
        days += prev_month_end.day
    if months < 0:
        years -= 1
        months += 12

    def unit(n, word):
        return f"{n} {word}{'' if n == 1 else 's'}"

    return f"{unit(years, 'year')}, {unit(months, 'month')}, {unit(days, 'day')}"


# 한 줄은 (텍스트, 색 이름) 조각들의 리스트다.
def field(key, value, width=COLS):
    dots = width - len(key) - len(value) - 3  # ":" + 점선 양옆 공백
    if dots < 1:
        raise ValueError(f"'{key}: {value}' does not fit in {width} cols")
    return [(f"{key}:", "key"), (f" {'.' * dots} ", "dots"), (value, "value")]


def pair(left, right):
    half = (COLS - 3) // 2
    return field(*left, width=half) + [(" | ", "text")] + field(*right, width=COLS - 3 - half)


def header(title):
    return [(f"{title} ", "text"), ("─" * (COLS - len(title) - 1), "text")]


def info_lines(stats, today):
    s = stats
    return [
        header("birdust@github"),
        field("OS", "Ubuntu 24.04, CentOS 7, Windows, Jetson Xavier NX"),
        field("Uptime", uptime(today)),
        field("Host", "SAIG · Traffic Control Backend"),
        field("Kernel", "Information & Communication"),
        field("IDE", "IntelliJ IDEA, VSCode, vim, Jupyter Notebook"),
        [],
        field("Languages.Programming", "Java, Python, JavaScript, SQL"),
        field("Frameworks.Backend", "Spring Boot, Spring AI, JPA, MyBatis"),
        field("Frameworks.Node", "NestJS"),
        field("Frameworks.Vision", "OpenCV, YOLO, PyTorch, ROS"),
        field("Infra.DB", "PostgreSQL, Redis, MySQL"),
        field("Infra.Ops", "Docker, nginx, GitHub Actions, Prometheus"),
        [],
        header("- Contact"),
        field("Email", "djswl0922@gmail.com"),
        field("Resume", "birdust.github.io/resume"),
        [],
        header("- GitHub Stats"),
        pair(("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}"), ("Stars", f"{s['stars']:,}")),
        pair(("Commits", f"{s['commits']:,}"), ("Followers", f"{s['followers']:,}")),
    ]


def render(theme, lines):
    c = THEMES[theme]
    rows = max(len(lines), len(CAT))
    height = rows * LINE_H + 30
    width = round(INFO_X + COLS * CHAR_W + 20)
    art_top = 30 + (rows - len(CAT)) // 2 * LINE_H  # 고양이는 세로 가운데

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-size="16px" '
        f"font-family=\"Consolas, 'DejaVu Sans Mono', Menlo, 'Courier New', monospace\">",
        "<style>",
        "text, tspan { white-space: pre; }",
        *(f".{name} {{ fill: {color}; }}" for name, color in c.items() if name != "bg"),
        "</style>",
        f'<rect width="{width}" height="{height}" rx="15" fill="{c["bg"]}"/>',
        '<text class="art">',
        *(
            f'<tspan x="{ART_X}" y="{art_top + i * LINE_H}">{escape(line)}</tspan>'
            for i, line in enumerate(CAT)
        ),
        "</text>",
        '<text class="text">',
    ]
    for i, parts in enumerate(lines):
        if not parts:
            continue
        spans = "".join(f'<tspan class="{cls}">{escape(txt)}</tspan>' for txt, cls in parts)
        out.append(f'<tspan x="{INFO_X}" y="{30 + i * LINE_H}">{spans}</tspan>')
    out += ["</text>", "</svg>", ""]
    return "\n".join(out)


def main():
    today = datetime.now(KST).date()
    lines = info_lines(fetch_stats(), today)
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(render(theme, lines), encoding="utf-8")
        print(f"wrote {theme}_mode.svg")


if __name__ == "__main__":
    main()

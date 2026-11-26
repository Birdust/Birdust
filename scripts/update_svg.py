"""neofetch 스타일 프로필 카드(dark_mode.svg / light_mode.svg)를 생성한다.

GitHub Actions에서 매일 실행되어 Uptime을 갱신한다.
표준 라이브러리만 사용한다.

    python scripts/update_svg.py
"""

from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

BIRTHDAY = date(2001, 9, 22)
KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]

# 오른쪽 정보 영역 폭(글자 수). 점선으로 값 끝을 이 폭에 맞춘다.
COLS = 58
CHAR_W = 9.7  # 16px 고정폭 폰트 한 글자 폭(넉넉하게 잡은 값)
ART_CHAR_W = 8.8  # 고양이 가운데 정렬용 평균 글자 폭(Consolas 기준)
LINE_H = 20
INFO_X = 400

CAT = r"""
  _____________
 < Hello world >
  -------------
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
def field(key, value):
    dots = COLS - len(key) - len(value) - 3  # ":" + 점선 양옆 공백
    if dots < 1:
        raise ValueError(f"'{key}: {value}' does not fit in {COLS} cols")
    return [(f"{key}:", "key"), (f" {'.' * dots} ", "dots"), (value, "value")]


def header(title):
    return [(f"{title} ", "text"), ("─" * (COLS - len(title) - 1), "text")]


def info_lines(today):
    return [
        header("birdust@github"),
        field("OS", "Ubuntu 24.04, CentOS 7, Windows, Jetson Xavier NX"),
        field("Uptime", uptime(today)),
        field("Host", "SAIG · Traffic Control Backend"),
        field("Kernel", "Information & Communication"),
        field("IDE", "IntelliJ IDEA, VSCode, vim, Jupyter Notebook"),
        [],
        field("Languages", "Java, Python, JavaScript, SQL"),
        field("Frameworks", "Spring Boot, NestJS, Node.js, React, FastAPI"),
        field("Vision", "OpenCV, YOLO, PyTorch, ROS"),
        field("Database", "PostgreSQL, Redis, MySQL"),
        field("DevOps", "Docker, nginx, GitHub Actions"),
        [],
        header("- Contact"),
        field("Email", "djswl0922@gmail.com"),
        field("Resume", "birdust.github.io/resume"),
    ]


def render(theme, lines):
    c = THEMES[theme]
    rows = max(len(lines), len(CAT))
    height = rows * LINE_H + 30
    width = round(INFO_X + COLS * CHAR_W + 20)
    # 고양이는 왼쪽 영역의 가로·세로 가운데
    art_x = round((INFO_X - max(map(len, CAT)) * ART_CHAR_W) / 2)
    art_top = 30 + (rows - len(CAT)) // 2 * LINE_H

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
            f'<tspan x="{art_x}" y="{art_top + i * LINE_H}">{escape(line)}</tspan>'
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
    lines = info_lines(datetime.now(KST).date())
    for theme in THEMES:
        # OS와 상관없이 LF로 써야 로컬 실행과 Actions 결과가 같아진다.
        (ROOT / f"{theme}_mode.svg").write_text(render(theme, lines), encoding="utf-8", newline="\n")
        print(f"wrote {theme}_mode.svg")


if __name__ == "__main__":
    main()

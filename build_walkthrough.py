#!/usr/bin/env python3
"""Render the Workflow Walkthrough page: two walkthrough videos, short then full.

The page is the masthead and the two players, nothing else. Each video lives in
assets/walkthrough/ as an H.264 MP4 small enough for GitHub (under 50 MB), with
a poster frame (the title card) shown before it plays.
"""

from pathlib import Path

import build_time_motion
import theme
from theme import GENERATED, esc

ROOT = Path(__file__).parent
SLUG = "walkthrough"
SUBLINE = "AI-assisted handover: inspections, snagging, rectification, checks and sign-offs."

# The videos, in page order: (title, video, poster, duration).
VIDEOS = [
    ("AI-Powered Snagging & De-snagging: Pilot Walkthrough",
     "assets/walkthrough/ai-assisted-handover-walkthrough.mp4",
     "assets/walkthrough/poster.jpg", "3 min 47 s"),
    ("AI-Powered Handover Pipeline: Full Workflow",
     "assets/walkthrough/full-workflow.mp4",
     "assets/walkthrough/poster-full.jpg", "4 min 48 s"),
]

PAGE_CSS = """
.player{background:#000;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.player video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#000}
"""


def player(title, video, poster, duration):
    return f"""<section class="card">
  <div class="card-head">
    <h2>{esc(title)}</h2>
    <p class="card-sub">{duration}</p>
  </div>
  <div class="player">
    <video controls preload="metadata" playsinline poster="{poster}">
      <source src="{video}" type="video/mp4">
      Your browser cannot play this video. <a href="{video}">Download it</a> instead.
    </video>
  </div>
</section>"""


def render():
    masthead = theme.masthead(SLUG, "Workflow Walkthrough", SUBLINE, "<b>Videos</b>")
    players = "\n\n".join(player(*v) for v in VIDEOS)
    files = " &middot; ".join(f'<span class="mono">{v[1]}</span>' for v in VIDEOS)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>DAMAC snagging pilot &mdash; Workflow Walkthrough</title>
<meta name="description" content="The AI-assisted handover workflow, from inspections to sign-offs: a short pilot walkthrough and the full workflow.">
<style>
{theme.CHROME_CSS}

{PAGE_CSS}
</style>
</head>
<body>
<div class="wrap">

{masthead}

{players}

<p class="foot">
  {files} &middot; page by
  <span class="mono">build_walkthrough.py</span> &middot; {GENERATED:%d %b %Y}.
</p>

</div>
</body>
</html>
"""


def main():
    missing = [p for _, v, poster, _ in VIDEOS for p in (v, poster)
               if not (ROOT / p).is_file()]
    assert not missing, f"missing: {', '.join(missing)}"
    out = ROOT / build_time_motion.page_file(SLUG)
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the Workflow Walkthrough page: the AI-assisted handover walkthrough video.

The page is the masthead and the video, nothing else. The video lives in
assets/walkthrough/ as an H.264 MP4 small enough for GitHub (under 50 MB), with
a poster frame shown before it plays.
"""

from pathlib import Path

import build_time_motion
import theme
from theme import GENERATED

ROOT = Path(__file__).parent
SLUG = "walkthrough"
VIDEO = "assets/walkthrough/ai-assisted-handover-walkthrough.mp4"
POSTER = "assets/walkthrough/poster.jpg"
SUBLINE = "AI-assisted handover: inspections, snagging, rectification, checks and sign-offs."

PAGE_CSS = """
.player{background:#000;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.player video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#000}
"""


def render():
    masthead = theme.masthead(SLUG, "Workflow Walkthrough", SUBLINE, "<b>Video</b>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>DAMAC snagging pilot &mdash; Workflow Walkthrough</title>
<meta name="description" content="The AI-assisted handover workflow, from inspections to sign-offs, in one video.">
<style>
{theme.CHROME_CSS}

{PAGE_CSS}
</style>
</head>
<body>
<div class="wrap">

{masthead}

<section class="player">
  <video controls preload="metadata" playsinline poster="{POSTER}">
    <source src="{VIDEO}" type="video/mp4">
    Your browser cannot play this video. <a href="{VIDEO}">Download it</a> instead.
  </video>
</section>

<p class="foot">
  <span class="mono">{VIDEO}</span> &middot; page by
  <span class="mono">build_walkthrough.py</span> &middot; {GENERATED:%d %b %Y}.
</p>

</div>
</body>
</html>
"""


def main():
    missing = [p for p in (VIDEO, POSTER) if not (ROOT / p).is_file()]
    assert not missing, f"missing: {', '.join(missing)}"
    out = ROOT / build_time_motion.page_file(SLUG)
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

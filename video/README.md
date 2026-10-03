# Video tutorial

A narrated walkthrough of this project, built from code out of the real recordings of the build: Terraform output,
the GitHub Actions runs, kubectl and curl against the live cluster, the attacks, and the verified teardown.

| File | What it is |
|---|---|
| `scenes.py` | the script: scenes, narration steps, and the visuals for each step |
| `components.py` | building blocks: cards, tiles, diagrams, highlighted code excerpts, terminals |
| `redact.py` | removes account IDs, private e-mail addresses and organisation names; the build fails if any remain |
| `build.py` | page → frames → narration → encode → captions, chapters and description |
| `shot.mjs` | screenshots the scenes with one headless Edge/Chrome (DevTools protocol) |
| `tts.ps1` | narrates each step offline with `System.Speech` (Windows) |
| `thumbnail.html` | the YouTube thumbnail (1280×720) |
| `assets/` | screenshots taken during the build (the live app, the GitHub Actions run) |
| `youtube/` | upload package: title options, description with chapters, tags, captions (SRT), thumbnail, pinned comment |

## Build

Requirements: Windows (for `System.Speech`), Python 3 with `pygments` and `Pillow`, Node.js 22+, Microsoft Edge (or
set `BROWSER`), and Docker (ffmpeg runs in a container pinned by digest).

```bash
python video/build.py            # everything; output: video/out/video.mp4
python video/build.py frames     # only re-render the visuals after editing scenes.py
python video/build.py audio      # only re-narrate (VOICE="Microsoft Zira Desktop" SPEED=1 to change the voice)
python video/build.py video      # only re-encode, and rewrite captions, chapters and the description
```

## Privacy

The recordings come from a real AWS account. Every text that reaches a frame, the narration, the captions or the
description goes through `redact.py`: 12-digit account IDs (also inside ARNs and ECR hostnames), e-mail addresses
other than the author's public one, and organisation names (`REDACT_WORDS` adds more). After redaction the build
checks the page, captions, chapters and description again and stops if anything identifying is left.

## Upload checklist

1. Upload `out/video.mp4`; use the first title in `youtube/title.txt`.
2. Paste `youtube/description.md` (its chapter list becomes YouTube chapters).
3. Thumbnail `youtube/thumbnail.png`; tags from `youtube/tags.txt`.
4. Subtitles: upload `youtube/captions.srt` (English).
5. Pin the comment in `youtube/pinned-comment.txt`.

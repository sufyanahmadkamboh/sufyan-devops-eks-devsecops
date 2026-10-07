# Video tutorials

> The YouTube upload package (`youtube/`) is written by the build and kept locally; it is not published in this repository.

There are two:

- **The project video** (`scenes.py`, 23 minutes): the whole build, the attacks and the teardown, in one go.
- **The two-part workshop** (`scenes_part1.py`, `scenes_part2.py`): a slower, practical walkthrough recorded live on
  a real AWS account. Part 1 covers the problem, the architecture, the repository, Terraform, the VPC and the EKS
  cluster, an AWS Console tour (read-only session), and the image build, scan, SBOM and signing. Part 2 covers GitHub OIDC,
  every pipeline stage, a real push going live, a dependency vulnerability stopped by the pipeline, a broken rollout
  troubleshot layer by layer, production improvements, cost, and the verified teardown.

Each video is a narrated walkthrough of this project, built from code out of the real recordings of the build: Terraform output,
the GitHub Actions runs, kubectl and curl against the live cluster, the attacks, and the verified teardown.

| File | What it is |
|---|---|
| `scenes.py` | the project video's script: scenes, narration steps, and the visuals for each step |
| `scenes_part1.py`, `scenes_part2.py` | the two workshop parts |
| `components.py` | building blocks: cards, tiles, diagrams, highlighted code excerpts, terminals |
| `redact.py` | removes account IDs, private e-mail addresses and organisation names; the build fails if any remain |
| `build.py` | page → frames → narration → encode → captions, chapters and description |
| `shot.mjs` | screenshots the scenes with one headless Edge/Chrome (DevTools protocol) |
| `tts.ps1` | narrates each step offline with `System.Speech` (Windows) |
| `thumbnail.html`, `thumbnail_part1.html`, `thumbnail_part2.html` | the YouTube thumbnails (1280×720) |
| `assets/` | screenshots taken during the build; `assets/workshop/` holds the workshop's AWS Console and GitHub screenshots |
| `youtube/`, `youtube/part1/`, `youtube/part2/` | upload packages: title options, description with chapters, tags, captions (SRT), thumbnail, pinned comment |

## Build

Requirements: Windows (for `System.Speech`), Python 3 with `pygments` and `Pillow`, Node.js 22+, Microsoft Edge (or
set `BROWSER`), and Docker (ffmpeg runs in a container pinned by digest).

```bash
python video/build.py            # everything; output: video/out/video.mp4
python video/build.py frames     # only re-render the visuals after editing scenes.py
python video/build.py audio      # only re-narrate (VOICE="Microsoft Zira Desktop" SPEED=1 to change the voice)
python video/build.py video      # only re-encode, and rewrite captions, chapters and the description

PART=1 python video/build.py     # workshop part 1: video/out/part1/video.mp4, package in video/youtube/part1/
PART=2 python video/build.py     # workshop part 2
```

## Privacy

The recordings come from a real AWS account. Every text that reaches a frame, the narration, the captions or the
description goes through `redact.py`: 12-digit account IDs (also inside ARNs and ECR hostnames), e-mail addresses
other than the author's public one, and organisation names (`REDACT_WORDS` adds more). After redaction the build
checks the page, captions, chapters and description again and stops if anything identifying is left.

The AWS Console screenshots in the workshop were taken in a federated session limited to `ReadOnlyAccess`. Identifying
text was replaced inside the page (in every frame, including embedded ones) before each screenshot, and every image was
then checked with OCR for account IDs, e-mail addresses and organisation names before it was used.

## Upload checklist

For the workshop, replace `{{PART1_LINK}}` / `{{PART2_LINK}}` in the part descriptions and pinned comments with
the video links after uploading, and add both parts to one playlist.

1. Upload `out/video.mp4` (or `out/partN/video.mp4`); use the first title in `youtube/title.txt`.
2. Paste `youtube/description.md` (its chapter list becomes YouTube chapters).
3. Thumbnail `youtube/thumbnail.png`; tags from `youtube/tags.txt`.
4. Subtitles: upload `youtube/captions.srt` (English).
5. Pin the comment in `youtube/pinned-comment.txt`.

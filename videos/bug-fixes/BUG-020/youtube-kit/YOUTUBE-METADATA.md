# BUG-020 YouTube Upload Kit

## Title
BUG-020: Live Bug Fix -- Button Styling Broken in Production (Human + AI)

## Description
(copy everything below the line into YouTube description)
---

A real bug fix captured live on screen. No scripts, no staging -- just a developer and an AI co-pilot (Claude Code) finding, fixing, deploying, and verifying a CSS bug on a production system.

The bug: All buttons in ISOTTO Sport (a print shop management app) lost their styling -- no background colors, no hover effects, no rounded corners. Every .btn-primary, .btn-secondary, and .btn-success rendered as plain unstyled HTML.

The fix: One line change in base.html
- Before: <style>
- After: <style type="text/tailwindcss">

The Tailwind CDN script needs type="text/tailwindcss" to process @apply directives. Without it, all custom button classes were silently ignored.

What you see in this video:
0:00 - Intro
0:08 - Login to ISOTTO Sport on live server
0:40 - QA Dashboard showing 47 test cases, 12 open bugs
1:10 - BUG-020 report with annotated screenshot
2:28 - THE FIX -- one line CSS change
2:55 - Code diff in VS Code
3:15 - Git push, deploy to Hetzner, smoke test
4:21 - AFTER -- buttons properly styled
7:06 - Bug verified and closed in QA dashboard
7:49 - Done

Tech stack: FastAPI, Jinja2 templates, Tailwind CSS (CDN), Keycloak OIDC, Docker, Hetzner Cloud

Built with HelixNet -- an open platform for Swiss SMEs
AI co-pilot: Claude Code by Anthropic

---

## Tags
(comma-separated, copy into YouTube)
---
bug fix,live bug fix,css bug,tailwind css,button styling,web development,fullstack,fastapi,python,jinja2,docker,hetzner,keycloak,devops,deploy,smoke test,qa testing,human and ai,ai coding,claude code,anthropic,pair programming,ai pair programming,real time coding,production bug,helixnet,isotto,print management,one line fix,css fix,tailwindcss cdn,developer workflow,bug tracking,software engineering,live coding
---

## Category
Science and Technology

## Visibility
Public

## Language
English

## Chapters (paste into description if desired)
0:00 Intro
0:08 Login to ISOTTO Sport
0:40 QA Dashboard -- 12 Open Bugs
1:10 BUG-020 -- Button Styling Broken
2:28 Step 2: The Fix
2:55 Code Change in VS Code
3:15 Deploy to Production
4:21 Step 3: Deployed -- 52 Passed
4:24 AFTER -- Buttons Fixed
7:06 Step 4: Verified
7:49 Outro

## Thumbnail
thumbnail.jpg (1280x720, YouTube recommended size)

## Subtitles
voice-final-limited.srt (upload as English captions)

## Files in this kit
- YOUTUBE-METADATA.md -- this file
- thumbnail.html -- source for thumbnail
- thumbnail.png -- high quality thumbnail
- thumbnail.jpg -- YouTube upload thumbnail
- voice-final-limited.srt -- English subtitles/captions
- description.txt -- ready-to-paste YouTube description
- tags.txt -- ready-to-paste tags

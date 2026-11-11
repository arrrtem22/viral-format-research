---
name: viral-format-research
description: Research a niche on TikTok to find content formats you can copy to market an app. Scrape the buyer's search terms with Apify, keep posts with 100x views per follower on small accounts, group slideshows and videos into formats seen on 3+ accounts, and write one short CSV that says whether the niche runs on slideshows or video, and whether the winners can be copied (hook + demo, silent UGC) or need a face or a known brand. Use for "research viral formats for X", "same research for <app/niche>", or "does <niche> work on TikTok".
---

# Viral format research

The research covers the whole niche, both slideshows and videos. It answers 3 questions:
1. Does the niche run on slideshows, video or both?
2. Can a new account copy the winners as a slideshow, a 3-second hook + app demo, or silent UGC (hands, screen recording, no face)? Or do they need a face, a voice or a trusted brand?
3. Which formats should go on which accounts?

`example/bible_viral_formats.csv` shows the output. Paths to `scripts/` and `example/` below are relative to the folder this SKILL.md is in.

## Steps

1. **Pick 14 to 16 search terms aimed at the buyer, not the topic.** For a calorie tracker, search "weight loss", "what i eat in a day" and "calorie deficit", not "calorie app". Add the buyer's pain points and the names of competitor apps ("character ai alternative" for an AI chat app).
   - 10 to 12 of the terms must be broad category terms that many people search ("homes for sale", "apartment tour"). Most of the hits come from these.
   - At most 4 terms can be narrow: a city, a brand or one product ("austin homes for sale"). Narrow terms return few posts and few hits.
   - Put the broad terms first. When the dollar cap ends the run early, the last terms come back short.
2. **Scrape.** A run costs about $3 to $5. Tell the user the dollar cap in one line before you start it.
   `scripts/scrape.sh outputs/research/<name> 55 5 "term 1" "term 2" ...`
   The script runs the Apify actor `clockworks~tiktok-scraper` (TikTok search, US proxy) and uses `$APIFY_TOKEN`, or the first key in `$APIFY_TOKENS_FILE` (default `~/.apify_tokens.txt`) that still has credit.
3. **Filter and draw the cover sheets.**
   `python3 scripts/analyze.py outputs/research/<name>/main.json outputs/research/<name>`
   A hit has 100x views per follower or more and at least 10,000 views, on an account with 100k followers or fewer. The script prints two `COUNTS` lines for the verdict and writes `hits.json` plus cover grids `slide_sheetN.jpg` and `video_sheetN.jpg`. It needs Pillow.
   The script also prints one `TERM` line per search term and marks a term `SHORT` when it returned under half the posts of the fullest term. A broad term marked `SHORT` means the dollar cap ended the run before that term finished.
   When the script prints `THIN` (fewer than 50 hits), do not write the CSV yet. Tell the user the extra $3 cap, then scrape 6 new broad terms plus any broad term marked `SHORT`, and analyze both files together:
   `scripts/scrape.sh outputs/research/<name>/more 55 3 "term 1" "term 2" ...`
   `python3 scripts/analyze.py outputs/research/<name>/main.json outputs/research/<name>/more/main.json outputs/research/<name>`
   Do this once. If the script still prints `THIN`, write the CSV and state the hit count in the `Runs on` line.
4. **Look at every sheet, slideshows and videos alike.** Group the hits into formats. A format counts only when it shows up on 3 or more different accounts. Tag each video format with how it can be copied:
   - `silent`: hands, screen recording or b-roll with text on screen, no face and no voice
   - `hook+demo`: a 3-second text hook, then the app on screen
   - `face`: needs a person talking to the camera
   - `brand`: works only for big or trusted accounts
5. **Write `outputs/research/<name>/<name>_viral_formats.csv`** in the layout below.
6. **Tell the user** the verdict and the CSV path in 3 to 5 lines.

## CSV layout

Keep every cell short: facts and numbers, no adjectives like "powerful" or "great", no filler.

```
VERDICT
Runs on,<slideshows | video | both>. <a> of <b> slideshow hits from last 90 days; <c> of <d> video hits.
Copy,<what can be copied and how>. <what cannot: face / brand>.
Test,<formats to run, accounts per format>. <what to skip>.

SLIDESHOWS
Format,How it looks,What changes per post,Where the CTA goes,Hook (on-screen),Link,Followers,Views,Views/follower,Posted,Search word
S1 <name>,<cover + slide pattern; max 15 words>,<what a new post swaps; max 10 words>,<slide number or caption, and how the app shows>,,,,,,,
,,,,<hook text>,<link>,<followers>,<views>,<ratio>x,<YYYY-MM-DD>,<term>

VIDEOS
Format,How it looks,What changes per post,Where the CTA goes,Hook (on-screen),Link,Followers,Views,Views/follower,Posted,Search word
V1 <name> (<silent | hook+demo | face | brand>),<shot pattern; max 15 words>,<what a new post swaps; max 10 words>,<second mark or caption, and how the app shows>,,,,,,,
,,,,<hook text>,<link>,<followers>,<views>,<ratio>x,<YYYY-MM-DD>,<term>
```

- Number formats S1, S2 … and V1, V2 …, best first: copyable, recent and a fit for the app.
- `What changes per post` is the part a new post swaps while the rest of the template stays the same (ranking: the app list; verse slideshow: the verses and the cover photo). Fill it only on the format row.
- `Where the CTA goes` is where the app shows and how: slide number (`slide 2, app screenshot`), second mark (`0:03, screen recording`), caption or pinned comment. Write `none` when the winners show no app. Fill it only on the format row.
- When the client sells something other than an app (a listing, a service, a physical product), read "app" in this layout as the offer. The CTA is then where the price, the phone number or the contact shows (`last slide, phone number`; `caption, price + agent contact`).
- Give each format 3 to 8 example rows, best ratio first. The first row is the post to copy.
- The hook is the text on screen or the first line of the caption, without hashtags.
- Leave out formats seen on fewer than 3 accounts. Leave out posts in other languages unless the app targets them.

## Rules

- Do not copy posts, spend on image generation, create accounts or post anything without the user's OK.
- Never write Apify tokens into chat or files. Show only the last 4 characters.

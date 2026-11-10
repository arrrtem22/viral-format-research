# viral-format-research

A Claude Code skill that tells you which TikTok formats to copy to market an app in a given niche.

You give it a niche, and it finds posts that got 100x more views than their account has followers. It groups those posts into formats that at least 3 different accounts used. Then it writes one CSV that answers:

- Does the niche run on slideshows, video or both?
- Can a new account copy the winners as a slideshow, a 3-second hook + app demo or silent UGC? Or do they need a face or a known brand?
- Which formats should you test, and on how many accounts?

I used it to plan TikTok accounts for apps in AI chat, calorie tracking, AI app building and Bible reading.

## Example output

The verdict at the top of [`skills/viral-format-research/example/bible_viral_formats.csv`](skills/viral-format-research/example/bible_viral_formats.csv):

```
Runs on,both. 6 of 49 slideshow hits from last 90 days; 7 of 30 video hits.
Copy,"slideshows S1-S4 + silent hands/screen video V1-V3. Winners 100-5k followers, no brand needed. V4 needs a face, skip."
Test,5 accts: S1 S2 S3 S4 one each + 1 acct V1/V2 (screen-record app). Skip S5 S6 V4.
```

Below the verdict, each format gets one row that says what it looks like, followed by example posts with hook, followers, views, views per follower, date and search term. The example keeps the posts for 2 formats per section and replaces creator handles with placeholders.

## How it works

1. Claude picks 10 to 16 search terms aimed at the buyer. For a calorie tracker that means "weight loss" and "what i eat in a day", not "calorie app".
2. `scripts/scrape.sh` runs the Apify actor [clockworks/tiktok-scraper](https://apify.com/clockworks/tiktok-scraper) on those terms. 450 posts cost about $2.
3. `scripts/analyze.py` keeps posts with 100x views per follower or more from accounts with 100k followers or fewer. It prints how many hits are from the last 90 days and draws cover grids of the hits.
4. Claude reads the cover grids, groups the hits into formats and tags each video format `silent`, `hook+demo`, `face` or `brand`.
5. Claude writes `<name>_viral_formats.csv` and gives you the verdict in a few lines.

## Install

In Claude Code:

```
/plugin marketplace add arrrtem22/viral-format-research
/plugin install viral-format-research@viral-format-research
```

Or with the [skills CLI](https://skills.sh), which also works for other agents:

```bash
npx skills add arrrtem22/viral-format-research
```

Then install Pillow for the cover grids:

```bash
pip install Pillow
```

You need an [Apify](https://apify.com) API token. Set `APIFY_TOKEN`, or put one or more tokens in `~/.apify_tokens.txt`. The script uses the first token that still has enough monthly credit for the run. Set `APIFY_TOKENS_FILE` to use another file.

## Use

In Claude Code:

```
/viral-format-research:viral-format-research meditation app for anxious students
```

With the skills CLI the command is `/viral-format-research`.

Claude can also start the skill on its own when you ask something like "does the Bible app niche work on TikTok?"

Claude asks before it spends money on Apify. It does not post, copy content or create accounts.

## Run the scripts by hand

From a clone of this repo:

```bash
cd skills/viral-format-research
scripts/scrape.sh out/meditation 30 2 "anxiety relief" "how to calm down" "study stress" "headspace"
python3 scripts/analyze.py out/meditation/main.json out/meditation
```

`scrape.sh` arguments: output folder, results per search term, spending cap in USD, then the search terms.

## License

MIT

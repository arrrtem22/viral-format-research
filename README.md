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

1. Claude asks whether to research slideshows, videos or both, then picks 14 to 16 search terms aimed at the buyer, most of them broad. For a calorie tracker that means "weight loss" and "what i eat in a day", not "calorie app".
2. `scripts/scrape.sh` runs the Apify actor [clockworks/tiktok-scraper](https://apify.com/clockworks/tiktok-scraper) on those terms. A run of about 800 posts costs $3 to $5.
3. `scripts/analyze.py` keeps posts with 100x views per follower or more and at least 10,000 views, from accounts with 100k followers or fewer. It prints how many hits are from the last 90 days and draws cover grids of the hits. It prints `THIN` when it finds fewer than 50 hits, and Claude then scrapes more broad terms.
4. Claude reads the cover grids, groups the hits into formats and tags each video format `silent`, `hook+demo`, `face` or `brand`.
5. Claude writes `<name>_viral_formats.csv` with a soft CTA for each format that a new account can repeat with endless variations.
6. `scripts/pick.py` marks the top 5 slideshow and top 5 video posts from those formats. Posts in the top 20% of views come first, best views per follower first, so a tiny account with a big ratio and little reach does not win. It saves an xlsx with those rows in green.
7. `scripts/upload_sheet.py` uploads the xlsx to Google Drive as a Google Sheet when gcloud is logged in with the Drive scope. Otherwise Claude asks whether to keep the local file or connect Google.
8. Claude gives you the verdict, the top picks and the sheet link in a few lines.

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

Then install Pillow for the cover grids and openpyxl for the xlsx:

```bash
pip install Pillow openpyxl
```

You need an [Apify](https://apify.com) API token. Set `APIFY_TOKEN`, or put one or more tokens in `~/.apify_tokens.txt`. The script uses the first token that still has enough monthly credit for the run. Set `APIFY_TOKENS_FILE` to use another file.

Google Sheets upload is optional. Log in once with the Drive scope, and turn on the Drive API in the quota project if the upload asks for it:

```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/cloud-platform
gcloud services enable drive.googleapis.com --project <quota project>
```

Sheets go to the Drive folder `Viral format research` (set `SHEETS_FOLDER` to change it). Set `GOOGLE_QUOTA_PROJECT` to use a project other than the one gcloud saved.

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
scripts/scrape.sh out/meditation 55 5 "anxiety relief" "how to calm down" "study stress" "headspace"
python3 scripts/analyze.py out/meditation/main.json out/meditation
```

`scrape.sh` arguments: output folder, results per search term, spending cap in USD, then the search terms.

## License

MIT

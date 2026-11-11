# Usage: analyze.py <main.json from scrape.sh> [more main.json ...] <outdir>
# Writes all.json, hits.json (slide + video hits, ranked) and slide/video contact sheets.
# Prints the counts line for the verdict and every hit (100x views/follower, <=100k followers, 10k+ views).
# Prints a THIN line when the sample is too small to trust: fewer than 50 hits. SHORT marks a term that came back with under half the posts of the fullest term.
import json, sys, datetime, io, urllib.request
from PIL import Image, ImageDraw
srcs, outdir = sys.argv[1:-1], sys.argv[-1]
MIN_VIEWS, MIN_HITS = 10000, 50
seen = {}
for src in srcs:
    for x in json.load(open(src)):
        if x.get('id') and x['id'] not in seen: seen[x['id']] = x
cut90 = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)).timestamp()
out = []
for x in seen.values():
    a = x.get('authorMeta') or {}; fans = a.get('fans') or 0; v = x.get('playCount') or 0
    out.append(dict(q=x.get('searchQuery'), slide=bool(x.get('isSlideshow')), recent=(x.get('createTime') or 0) >= cut90,
        date=(x.get('createTimeISO') or '')[:10], views=v, fans=fans, ratio=v / max(fans, 1), handle=a.get('name') or '',
        url=x.get('webVideoUrl'), cover=(x.get('videoMeta') or {}).get('coverUrl'), text=(x.get('text') or '').replace('\n', ' ')[:140],
        verified=bool(a.get('verified')), secs=(x.get('videoMeta') or {}).get('duration')))
json.dump(out, open(outdir + '/all.json', 'w'))
hit = lambda o: o['ratio'] >= 100 and o['fans'] <= 100000 and o['views'] >= MIN_VIEWS
allhits = {}
for kind in ('slide', 'video'):
    allhits[kind] = sorted([o for o in out if o['slide'] == (kind == 'slide') and hit(o)], key=lambda o: -o['views'])
json.dump(allhits, open(outdir + '/hits.json', 'w'))
print('total', len(out), 'slides', sum(o['slide'] for o in out), 'videos', sum(not o['slide'] for o in out))
for kind in ('slide', 'video'):
    h = allhits[kind]
    print(f"COUNTS {kind}: {sum(o['recent'] for o in h)} of {len(h)} {kind} hits from last 90 days")
terms = {}
for o in out:
    t = terms.setdefault(o['q'], [0, 0]); t[0] += 1; t[1] += hit(o)
full = max((t[0] for t in terms.values()), default=0)
short = [q for q, t in terms.items() if t[0] < full / 2]
for q, t in sorted(terms.items(), key=lambda kv: -kv[1][0]):
    print(f"TERM {t[0]:>4} posts {t[1]:>3} hits  {q}{'  SHORT' if q in short else ''}")
nhits = sum(len(h) for h in allhits.values())
if nhits < MIN_HITS:
    print(f"THIN: {nhits} hits (need {MIN_HITS}), {len(short)} short terms. Scrape more broad terms once. If it is still thin, write the hit count in the verdict.")
for kind in ('slide', 'video'):
    hits = allhits[kind]
    print(f'== {kind} hits:', len(hits), 'recent:', sum(o['recent'] for o in hits))
    for i, o in enumerate(hits):
        print(f"{i:>2} {'R' if o['recent'] else ' '} {o['views']:>9} {o['fans']:>7} {o['ratio']:>6.0f}x {o['date']} @{o['handle']} [{o['q']}] {o['text'][:100]}")
    W, H, cols = 240, 320, 6
    for p in range(0, len(hits), 24):
        ch = hits[p:p+24]
        sh = Image.new('RGB', (cols*W, ((len(ch)+cols-1)//cols)*(H+20)), 'white'); dr = ImageDraw.Draw(sh)
        for i, o in enumerate(ch):
            try:
                im = Image.open(io.BytesIO(urllib.request.urlopen(o['cover'], timeout=20).read())).convert('RGB'); im.thumbnail((W, H))
                sh.paste(im, ((i%cols)*W, (i//cols)*(H+20)))
            except Exception: pass
            dr.text(((i%cols)*W+2, (i//cols)*(H+20)+H+2), f"{p+i} @{o['handle'][:14]} {o['views']//1000}k", fill='black')
        sh.save(f'{outdir}/{kind}_sheet{p//24}.jpg', quality=70)

# Usage: analyze.py <main.json from scrape.sh> <outdir>
# Writes all.json, hits.json (slide + video hits, ranked) and slide/video contact sheets.
# Prints the counts line for the verdict and every hit (100x views/follower, <=100k followers).
import json, sys, datetime, io, urllib.request
from PIL import Image, ImageDraw
src, outdir = sys.argv[1], sys.argv[2]
seen = {}
for x in json.load(open(src)):
    if x.get('id') and x['id'] not in seen: seen[x['id']] = x
cut90 = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)).timestamp()
out = []
for x in seen.values():
    a = x.get('authorMeta') or {}; fans = a.get('fans') or 0; v = x.get('playCount') or 0
    out.append(dict(q=x.get('searchQuery'), slide=bool(x.get('isSlideshow')), recent=(x.get('createTime') or 0) >= cut90,
        date=(x.get('createTimeISO') or '')[:10], views=v, fans=fans, ratio=v / max(fans, 1), handle=a.get('name'),
        url=x.get('webVideoUrl'), cover=(x.get('videoMeta') or {}).get('coverUrl'), text=(x.get('text') or '').replace('\n', ' ')[:140],
        verified=bool(a.get('verified')), secs=(x.get('videoMeta') or {}).get('duration')))
json.dump(out, open(outdir + '/all.json', 'w'))
hit = lambda o: o['ratio'] >= 100 and o['fans'] <= 100000
allhits = {}
for kind in ('slide', 'video'):
    allhits[kind] = sorted([o for o in out if o['slide'] == (kind == 'slide') and hit(o)], key=lambda o: -o['views'])
json.dump(allhits, open(outdir + '/hits.json', 'w'))
print('total', len(out), 'slides', sum(o['slide'] for o in out), 'videos', sum(not o['slide'] for o in out))
for kind in ('slide', 'video'):
    h = allhits[kind]
    print(f"COUNTS {kind}: {sum(o['recent'] for o in h)} of {len(h)} {kind} hits from last 90 days")
for kind in ('slide', 'video'):
    hits = sorted([o for o in out if o['slide'] == (kind == 'slide') and o['ratio'] >= 100 and o['fans'] <= 100000], key=lambda o: -o['views'])
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

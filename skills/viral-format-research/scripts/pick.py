# Usage: pick.py <name>_viral_formats.csv <hits.json>
# Marks the top 5 slideshow and top 5 video example rows to copy at scale, then writes
# <name>_viral_formats.xlsx next to the CSV with those rows filled green.
# Candidates: example rows under a format whose "Soft CTA" cell is filled and not "none"
# (a format a new account can repeat with endless variations and a soft CTA for the offer).
# Rank: rows in the top 20% of views among all hits of that kind (hits.json) come first, best
# views/follower first; the rest follow by views rank + ratio rank. This keeps a 30-follower
# account with a huge ratio but few views from beating a post with real reach.
# Rewrites the CSV's "Top pick" column (TOP 1..TOP 5) and is safe to run again.
import csv, json, sys, os
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font

TOP_N, VIEW_SHARE = 5, 0.2
src, hits_path = sys.argv[1], sys.argv[2]
rows = list(csv.reader(open(src, newline='', encoding='utf-8-sig')))
hits = json.load(open(hits_path))


def num(v):
    v = (v or '').strip().rstrip('x').replace(',', '')
    mult = {'M': 1e6, 'k': 1e3, 'K': 1e3}.get(v[-1:], 1)
    try:
        return float(v[:-1] if mult != 1 else v) * mult
    except ValueError:
        return None


def is_format(r):
    return bool(r) and len(r[0]) > 1 and r[0][0] in 'SV' and r[0][1].isdigit()


NEED = ('Link', 'Views', 'Views/follower', 'Soft CTA', 'Top pick')
head, section, fmt, cta_ok = None, None, None, False
cand, row_head = {'S': [], 'V': []}, {}
for i, r in enumerate(rows):
    if r[:1] == ['Format']:
        missing = [c for c in NEED if c not in r]
        if missing:
            sys.exit(f'CSV header row {i + 1} lacks {missing} (see SKILL.md CSV layout)')
        head = {name: n for n, name in enumerate(r)}
        continue
    if r and r[0] in ('SLIDESHOWS', 'VIDEOS'):
        section, head = r[0][0], None
        continue
    if not head:
        continue
    row_head[i] = head
    cell = lambda name: r[head[name]].strip() if len(r) > head[name] else ''
    if is_format(r):
        fmt = r[0].split()[0]
        cta_ok = cell('Soft CTA').lower() not in ('', 'none')
    elif section and cta_ok and r and r[0] == '' and cell('Link').startswith('http'):
        views, ratio = num(cell('Views')), num(cell('Views/follower'))
        if views is not None and ratio is not None:
            cand[section].append(dict(row=i, url=cell('Link'), views=views, ratio=ratio, fmt=fmt))

picks, order = {}, []
for sec, kind in (('S', 'slide'), ('V', 'video')):
    seen, lst = set(), []
    for c in cand[sec]:
        if c['url'] not in seen:
            seen.add(c['url']); lst.append(c)
    views_all = sorted((o['views'] for o in hits.get(kind, [])), reverse=True)
    cut = views_all[max(0, int(len(views_all) * VIEW_SHARE) - 1)] if views_all else float('inf')
    top = sorted((c for c in lst if c['views'] >= cut), key=lambda c: -c['ratio'])
    rest = [c for c in lst if c['views'] < cut]
    # Tied values share a rank, so CSV order never decides a tie.
    vr = {c['url']: sum(o['views'] > c['views'] for o in rest) for c in rest}
    rr = {c['url']: sum(o['ratio'] > c['ratio'] for o in rest) for c in rest}
    rest.sort(key=lambda c: (vr[c['url']] + rr[c['url']], -c['views'], -c['ratio']))
    for n, c in enumerate((top + rest)[:TOP_N], 1):
        picks[c['row']] = f'TOP {n}'
        order.append((kind, c['row']))
    print(f"{kind}: views cut {cut:,.0f} (top {VIEW_SHARE:.0%} of {len(views_all)} hits), {len(top)} candidates above it, {len(lst)} candidates")

for i, h in row_head.items():
    r, col = rows[i], h['Top pick']
    if r and (i in picks or len(r) > col):
        r += [''] * (col + 1 - len(r))
        r[col] = picks.get(i, '')
with open(src, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)

wb = Workbook(); ws = wb.active; ws.title = 'Formats'
green, bold = PatternFill('solid', fgColor='C6EFCE'), Font(bold=True)
for i, r in enumerate(rows):
    ws.append([int(c) if c.isdigit() else c for c in r])
    if i in picks:
        for c in ws[ws.max_row]: c.fill = green
    if r and (r[0] in ('VERDICT', 'SLIDESHOWS', 'VIDEOS', 'Format') or is_format(r)):
        for c in ws[ws.max_row]: c.font = bold
for n, w in enumerate((34, 40, 28, 34, 48, 22, 10, 9, 9, 11, 22, 48, 9), 1):
    ws.column_dimensions[ws.cell(1, n).column_letter].width = w
xlsx = os.path.splitext(src)[0] + '.xlsx'
wb.save(xlsx)
for kind, i in order:
    r, h = rows[i], row_head[i]
    print(f"{kind} {picks[i]} {r[h['Views']]:>7} {r[h['Views/follower']]:>6} {r[h['Link']]}")
print('XLSX', xlsx)

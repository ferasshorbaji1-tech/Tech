"""Build Master_Leads_-_Cleanest_600.xlsx from the verified 600 + extras in the 1000 list."""
import pandas as pd, re, openpyxl
from urllib.parse import urlparse
from openpyxl.styles import Font
from collections import Counter

SOCIAL = re.compile(r'(facebook|tiktok|instagram|linktr\.ee|wixsite|sites\.google|site123|blogspot|canva\.site|scanned\.page|fato\.me|restaurantlogin|reach\.link|brand\.site|onelink|spyn\.co|web\.app|netlify|onrender|wuaze|wordpress\.com|inmyarea|preview-domain|linkedin|yellowpages|qatarliving|snoonu|talabat|qatarsale\.com)', re.I)
PLACE = re.compile(r'(example|@domain\.com|yourdomain|mysite|@email\.com|@company\.com$|support@support|sftp|\.webp|\.png|u002f|%20|gmil\.com|gmial\.com|noreply|wordpress@|^name@|^you@|^john@|^username@|^user@|^mail@example|^needhelp@|^promotors@|^yourteam@|^elcon@|sentry|wixpress|godaddy|latofonts|indiantypefoundry|impallari|rfuenzalida|houzez|eduweb|stagheaddesigns)', re.I)
FREE = re.compile(r'@(gmail|hotmail|yahoo|outlook|live|icloud)\.', re.I)
def host(u):
    try: h = urlparse(u if '://' in str(u) else 'http://'+str(u)).netloc.lower()
    except Exception: return ''
    return re.sub(r'^(www|m|en|order|rent|book|gcc|me|qa|signature)\.', '', h)
def root(h):
    p = h.split('.')
    if len(p)>=3 and p[-2] in ('com','co','net','org','edu','gov','sch'): return '.'.join(p[-3:])
    return '.'.join(p[-2:]) if len(p)>=2 else h
def brand(name):
    n = re.split(r'\s[-|(]\s|\s\|\s|\s-\s|\(|\|', str(name))[0]
    n = re.sub(r'[^A-Za-z0-9 ]', ' ', n).lower()
    n = re.sub(r'\b(the|cafe|café|coffee|restaurant|qatar|doha|branch|wll|w l l|llc|co|company|trading|and|&)\b', ' ', n)
    return re.sub(r'\s+', ' ', n).strip()

cols = ['#','Company','Category','Area','Phone','Email','Website','Address']
NONBIZ = {89,148,312,319,320,323,328,329,332,425,430,493}   # residences/compounds/site offices/person listing

def prep(df):
    d = df[cols].copy()
    for c in ('Email','Website','Address'):
        d[c] = d[c].fillna('').astype(str).str.replace('','').str.strip()
    d['wroot'] = d['Website'].map(lambda u: root(host(u)) if u else '')
    d['edom'] = d['Email'].map(lambda e: root(e.split('@')[-1].lower()) if '@' in e else '')
    d['brand'] = d['Company'].map(brand)
    d['social'] = d['Website'].map(lambda u: bool(SOCIAL.search(u)))
    d['junk'] = d['Email'].map(lambda e: bool(PLACE.search(e)))
    d['free'] = d['Email'].map(lambda e: bool(FREE.search(e)))
    d['match'] = (d['edom'] != '') & (d['edom'] == d['wroot'])
    return d

v = pd.read_excel('Master_Leads_-_Best_600_verified.xlsx')
k = pd.read_excel('Master_Leads_-_Cleanest_1000_original.xlsx')
orig = pd.read_excel('Master_Leads_-_Best_600_original.xlsx')

a = prep(v)
drop_reason, keep = {}, []
seen_email, seen_dom, seen_brand = set(), set(), set()
for _, r in a.iterrows():
    n = int(r['#']); why = None
    if n in NONBIZ: why = 'not a business (residence/compound/site office/person)'
    elif not r['Email']: why = 'no email'
    elif not r['Website']: why = 'no website'
    elif r['social']: why = 'website is a social/hosted page'
    elif r['junk']: why = 'junk email'
    elif r['Category'] == 'Cafe' and r['free']: why = 'small cafe (free-mail address only)'
    elif r['Email'].lower() in seen_email: why = 'duplicate (same email)'
    elif r['wroot'] and r['wroot'] in seen_dom: why = 'duplicate (same website)'
    elif r['brand'] and r['brand'] in seen_brand: why = 'duplicate (same brand)'
    if why: drop_reason[n] = why; continue
    seen_email.add(r['Email'].lower()); seen_dom.add(r['wroot']); seen_brand.add(r['brand'])
    keep.append(r)
kept = pd.DataFrame(keep)
print('kept from verified 600:', len(kept)); print(Counter(drop_reason.values()))

key = lambda d: (d['Company'].str.strip().str.lower() + '|' + d['Phone'].astype(str).str.strip())
ex = prep(k[~key(k).isin(set(key(orig)))].copy())
good = ex[(~ex['social']) & ex['match'] & (~ex['junk']) & (ex['Email']!='') & (ex['Website']!='')]
add = []
for _, r in good.iterrows():
    if r['Email'].lower() in seen_email or r['wroot'] in seen_dom or r['brand'] in seen_brand: continue
    seen_email.add(r['Email'].lower()); seen_dom.add(r['wroot']); seen_brand.add(r['brand'])
    add.append(r)
    if len(kept) + len(add) >= 600: break
added = pd.DataFrame(add)
print('added from extras:', len(added), '| good extras available:', len(good))
final = pd.concat([kept, added], ignore_index=True)[cols].copy(); final['#'] = range(1, len(final)+1)
print('final rows:', len(final), '| dup emails:', final['Email'].str.lower().duplicated().sum())

wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Leads'
ws.append(cols)
for c in ws[1]: c.font = Font(bold=True)
for row in final.itertuples(index=False): ws.append([x if x != '' else None for x in row])
for col, w in zip('ABCDEFGH', (5, 45, 28, 18, 16, 36, 45, 50)): ws.column_dimensions[col].width = w
ws.freeze_panes = 'A2'
wb.save('Master_Leads_-_Cleanest_600.xlsx')
pd.Series(drop_reason).to_csv('cleanest600_dropped.csv', header=['reason'])
print('saved')

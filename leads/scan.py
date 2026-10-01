import pandas as pd, re, json
from urllib.parse import urlparse

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Master_Leads_-_Best_600_original.xlsx')
OUT = '/tmp/claude-0/-home-user-Tech/4f4a12cb-2ddd-53fe-90bc-f52dccc25beb/scratchpad/scan.json'

df = pd.read_excel(SRC)

PLACEHOLDER_RE = re.compile(
    r'(example|domain|yourdomain|mysite|email\.com|company\.com|support@support|'
    r'sftp\.|\.webp|\.png|\.jpg|u002f|%20|gmil\.com|gmial\.com|noreply|no-reply|'
    r'wordpress@|onelink\.to|preview-domain|2x\.webp|^name@|^you@|^john@|^username@|^user@|^mail@example|'
    r'^needhelp@|^promotors@|^yourteam@|^elcon@|^contact@example|^info@example)', re.I)
# known third-party / template-origin addresses (font designers, theme vendors, agencies) that leak into scraped sites
KNOWN_JUNK = {
    'impallari@gmail.com', 'hello@rfuenzalida.com', 'jonpinhorn.typedesign@gmail.com', 'team@latofonts.com',
    'info@indiantypefoundry.com', 'micah@micahrich.com', 'ashley.lindsay@isobar.com', 'info@houzez.co',
    'info@eduweb.com', 'info@stagheaddesigns.com', 'eben@eyebytes.com', 'info@fitkit.com', 'pd@uaepd.net',
    'tsnym@tsnym.com', 'detach.roi@gmail.com', 'hempel@hempel.com', 'adsadver@emirates.net.ae',
    'weassure.uae@asianpaints.com', 'info@renovatioparis.com', 'cuanticdesignandreu@gmail.com',
    'info@mocozy.com', 'beatrootziamsec@gmail.com', 'mllegeorgesand@gmail.com', 'helmichouikh2311@gmail.com',
    'tech.ecmt@gmail.com', 'contact@sansoxygen.com', 'care@brookieno.com', 'hallysafety@yahoo.com',
    'maidslanka74@gmail.com', 'rentalinfo@vroomo.com', 'info@xtravel.com', 'asxvmprobertest@gmail.com',
    'razarusdei@gmail.com', 'aldahamcontractingwll@gmail.com', 'arabmarketingqa@gmail.com',
    'rashed.khan.rk143@gmail.com', 'sohagiphone11@gmail.com', 'fk5113832@gmail.com', 'mehadee1993@gmail.com',
    'mobarakhossain23456@gmail.com', 'malikrukhsar110@gmail.com', 'arifmeh41@gmail.com', 'dorce@dorce.com.tr',
    'azme@mzk-projct.com',
}
SOCIAL_RE = re.compile(r'(facebook\.com|tiktok\.com|instagram\.com|linktr\.ee|wixsite\.com|sites\.google\.com|'
                       r'site123\.me|blogspot\.com|canva\.site|scanned\.page|fato\.me|restaurantlogin\.com|'
                       r'reach\.link|brand\.site|onelink\.to|spyn\.co|web\.app|netlify\.app|onrender\.com|'
                       r'wuaze\.com|wordpress\.com|inmyarea\.in|preview-domain)', re.I)

def host(url):
    try:
        h = urlparse(url if '://' in url else 'http://' + url).netloc.lower()
    except Exception:
        return ''
    return re.sub(r'^(www|m|order|rent|book|gcc|me|qa)\.', '', h)

def root(h):
    # crude registrable-domain: drop one leading label if >2 labels and 2nd-level is short cc-style
    parts = h.split('.')
    if len(parts) >= 3 and parts[-2] in ('com', 'co', 'net', 'org', 'edu', 'gov'):
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:]) if len(parts) >= 2 else h

rows = []
for _, r in df.iterrows():
    email = str(r['Email']).strip()
    web = str(r['Website']).strip()
    edom = email.split('@')[-1].lower() if '@' in email else ''
    wh = host(web)
    flags = []
    if PLACEHOLDER_RE.search(email) or email.lower() in KNOWN_JUNK:
        flags.append('bogus_email')
    if SOCIAL_RE.search(web):
        flags.append('social_or_hosted_site')
    elif edom and wh and root(edom) != root(wh) and not edom.endswith(('gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com')):
        flags.append('email_domain_ne_site')
    if edom.endswith(('gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com')):
        flags.append('free_mail')
    rows.append({
        'n': int(r['#']), 'company': r['Company'], 'category': r['Category'], 'area': r['Area'],
        'phone': r['Phone'], 'email': email, 'website': web, 'check': r['Check'],
        'flags': flags,
    })

json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=0)
from collections import Counter
c = Counter(f for r in rows for f in r['flags'])
print(c)
print('rows with any flag:', sum(1 for r in rows if r['flags']))
print('rows with no flag  :', sum(1 for r in rows if not r['flags']))

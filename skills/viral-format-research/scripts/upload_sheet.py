# Usage: upload_sheet.py <file.xlsx> [title]
# Uploads the xlsx to Google Drive as a Google Sheet in the folder "Viral format research"
# ($SHEETS_FOLDER to change it). A sheet with the same title in that folder is updated in place,
# so its link stays the same. Cell colors carry over.
# Auth: gcloud Application Default Credentials with the drive.file scope, and a quota project
# ($GOOGLE_QUOTA_PROJECT, else quota_project_id from the ADC file) that has the Drive API enabled.
# Prints "SHEET <link>" and exits 0 on success.
# Exits 2 with "NOT CONNECTED: <reason>" when Google is not set up; SKILL.md says how to connect.
import json, os, shutil, subprocess, sys, urllib.parse, urllib.request, urllib.error, uuid

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
SHEET, FOLDER = 'application/vnd.google-apps.spreadsheet', 'application/vnd.google-apps.folder'
path = sys.argv[1]
title = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(path))[0]
folder_name = os.environ.get('SHEETS_FOLDER', 'Viral format research')


def not_connected(why):
    print(f'NOT CONNECTED: {why}')
    sys.exit(2)


if not shutil.which('gcloud'):
    not_connected('gcloud is not installed')
p = subprocess.run(['gcloud', 'auth', 'application-default', 'print-access-token'], capture_output=True, text=True)
if p.returncode or not p.stdout.strip():
    not_connected('no Google login (gcloud application-default credentials missing or expired)')
token = p.stdout.strip()
project = os.environ.get('GOOGLE_QUOTA_PROJECT')
if not project:
    adc = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    try:
        project = json.load(open(adc)).get('quota_project_id')
    except (OSError, ValueError):
        project = None
if not project:
    not_connected('no quota project (set GOOGLE_QUOTA_PROJECT or log in again with gcloud)')


def call(method, url, body=None, ctype=None):
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('x-goog-user-project', project)
    if ctype:
        req.add_header('Content-Type', ctype)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='replace')
        try:
            msg = json.loads(msg)['error']['message']
        except (ValueError, KeyError, TypeError):
            pass
        # 401 and setup 403s (API off, missing scope, bad project) mean "not connected";
        # rate limits and other failures are plain errors (exit 1).
        setup = e.code == 401 or (e.code in (400, 403) and any(
            k in str(msg).lower() for k in ('has not been used', 'is disabled', 'scope', 'permission', 'project')))
        if setup and 'rate limit' not in str(msg).lower():
            not_connected(f'Google said {e.code}: {msg[:300]}')
        sys.exit(f'Drive error {e.code}: {msg[:300]}')


def find(name, mime, parent=None):
    q = f"name = '{name.replace(chr(92), chr(92) * 2).replace(chr(39), chr(92) + chr(39))}' and mimeType = '{mime}' and trashed = false"
    if parent:
        q += f" and '{parent}' in parents"
    r = call('GET', 'https://www.googleapis.com/drive/v3/files?' + urllib.parse.urlencode({'q': q, 'fields': 'files(id)', 'spaces': 'drive'}))
    return r['files'][0]['id'] if r.get('files') else None


folder = find(folder_name, FOLDER) or call(
    'POST', 'https://www.googleapis.com/drive/v3/files?fields=id',
    json.dumps({'name': folder_name, 'mimeType': FOLDER}).encode(), 'application/json')['id']
data = open(path, 'rb').read()
existing = find(title, SHEET, folder)
if existing:
    r = call('PATCH', f'https://www.googleapis.com/upload/drive/v3/files/{existing}?uploadType=media&fields=id,webViewLink', data, XLSX)
else:
    b = uuid.uuid4().hex
    meta = json.dumps({'name': title, 'mimeType': SHEET, 'parents': [folder]})
    body = (f'--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n'
            f'--{b}\r\nContent-Type: {XLSX}\r\n\r\n').encode() + data + f'\r\n--{b}--\r\n'.encode()
    r = call('POST', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink', body, f'multipart/related; boundary={b}')
print('SHEET', r['webViewLink'])

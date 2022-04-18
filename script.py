from subprocess import Popen, PIPE
from datetime import datetime, timedelta
from ytmusicapi import YTMusic
import requests
import urllib.parse
import json
import re

def main():
    if not network_available():
        exit(1)

    now_playing = execute_script('''
        tell application "System Events"
            tell its application process "ControlCenter"
                click (first menu bar item whose name is "Now Playing") of menu bar 1
                set track to name of first static text of group 1 of first item of windows
                key code 53
                return track
            end tell
        end tell
    ''')

    print('now playing:')
    print(now_playing)

    ytmusic = YTMusic('ytm-auth.json')

    latest_track = ytmusic.get_history()[0]
    latest_title = latest_track['title']
    latest_artist = latest_track['artists'][0]['name']

    print('latest track:')
    print(latest_track)

    if any(blocked.lower() in latest_title.lower() for blocked in read_file_to_lines('blocklist.txt')):
        print("blocked")
        return

    simple_title = latest_title.split('(', 1)[0].split('/', 1)[0].strip()

    if not now_playing.startswith(simple_title):
        print("not currently playing")
        return

    subst_title = subst(simple_title)
    subst_artist = subst(latest_artist)
    (trunc_title, trunc_artist) = dualTruncate(subst_title, subst_artist)
    status = f'{trunc_title} - {trunc_artist}'
    print(f'setting status to: {status}')
    resp = set_status(status, 'headphones', 5)
    print(f'server response: {resp}')

def network_available():
    try:
        requests.head('https://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        print('Network unavailable')
    return False

def execute_script(script):
    process = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = process.communicate(script)
    print(stderr)
    return stdout


def read_file_to_lines(path):
    with open(path) as file:
        return [line.rstrip() for line in file]


def read_file_to_json(path):
    with open(path) as file:
        return json.load(file)


def subst(s):
    subs = read_file_to_json('substitutions.json')
    for key, val in subs.items():
        s = re.sub(key, val, s, flags=re.IGNORECASE)
    return s


def dualTruncate(a, b):
    # Slack max. status length is 100, and we add " - ", so that leaves us 97 characters
    if len(a) + len(b) > 97:
        if len(a) >= len(b):
            a = truncate(a)
        else:
            b = truncate(b)
        # Recurse until we're under 97
        return dualTruncate(a, b)
    else:
        return (a, b)


# Shave off one character, replace last three with ellipsis
def truncate(s):
    return s[:-4] + "..."


def urlencode(s):
    return urllib.parse.quote_plus(s)


def set_status(text, emoji, minutes):
    xc, xd, xds = read_har()
    expiry = round((datetime.now() + timedelta(minutes=minutes)).timestamp())
    cookies = {
        'd': urlencode(xd),
        'd-s': xds
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    profile = {
        "status_emoji": f':{emoji}:',
        "status_expiration": expiry,
        "status_text": text,
        "status_text_canonical": ""
    }
    body = f'profile={urlencode(json.dumps(profile))}&token={xc}'
    r = requests.post('https://amzn-aws.slack.com/api/users.profile.set', cookies=cookies, headers=headers, data=body)

    return r.json()

def read_har():
    data = read_file_to_json('slack-auth.har')
    request = data['log']['entries'][0]['request']
    postData = request['postData']['text']
    xc = re.search("xoxc-[^\\r]*", postData).group()
    cookies = request['cookies']
    xd = next(c['value'] for c in cookies if c['name'] == 'd')
    xds = next(c['value'] for c in cookies if c['name'] == 'd-s')
    return xc, xd, xds


main()

from subprocess import Popen, PIPE
from datetime import datetime, timedelta
from ytmusicapi import YTMusic
import requests
import urllib.parse
import json
import re

def main():
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

    latest_track = ytmusic.get_history()[0]['title']

    print('latest track:')
    print(latest_track)

    if any(blocked.lower() in latest_track.lower() for blocked in get_blocklist()):
        print("blocked")
        return

    if not now_playing.startswith(latest_track):
        print("not currently playing")
        return

    print("updating status")
    simple_title = latest_track.split('(', 1)[0].strip()
    set_status(simple_title, 'headphones', 6)


def execute_script(script):
    process = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = process.communicate(script)
    print(stderr)
    return stdout


def get_blocklist():
    with open('blocklist.txt') as file:
        return [line.rstrip() for line in file]


def urlencode(str):
    return urllib.parse.quote_plus(str)


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
    with open('slack-auth.har') as file:
        data = json.load(file)
    request = data['log']['entries'][0]['request']
    postData = request['postData']['text']
    xc = re.search("xoxc-[^\\r]*", postData).group()
    cookies = request['cookies']
    xd = next(c['value'] for c in cookies if c['name'] == 'd')
    xds = next(c['value'] for c in cookies if c['name'] == 'd-s')
    return xc, xd, xds


main()

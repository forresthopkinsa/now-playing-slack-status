# now-playing-slack-status
Update Slack status with Now Playing track from Mac menubar and Youtube Music

## Features

- Replicate Slack user-side API requests instead of using the developer API
  - This means the script can't be distributed as a Slack app
  - Critically, it also allows the script to be used without being added to the Slack organization
- Read "Now Playing" from Mac menubar using Applescript
  - Kinda clunky but it gets the job done
- Also reads the latest track from user's Youtube Music history
  - If it doesn't match the Mac "Now Playing" track, then we don't update the status
- Word blocklist
  - For when you don't want to announce that you're listening to Adele
- Substitutions
  - To sanitize the less corporate-friendly song titles or artist names in your collection

## Usage

There are three steps to set up the script:

1. Clone the repo
2. Youtube Music auth: download authorized headers ([instructions](https://ytmusicapi.readthedocs.io/en/latest/setup.html)) to a file `ytm-auth.json` in the repo directory.
3. Slack auth: log into the web UI and download an authenticated network request as `slack-auth.har` – see below:

![save-har](https://user-images.githubusercontent.com/4433153/163091629-1e9903eb-ebbe-49d4-a3cd-16e45cf8afed.gif)

And that's it for setup.

You can run the script manually:

```
python3 script.py
```

But there's also a shell script to make cron jobs trivial:

```
*/4 9-16 * * 1-5 /path/to/now-playing-slack-status/run.sh
```

The above runs the script every four minutes on weekdays from 9:00am - 4:56pm.
The shell script writes output to a log file.
If the cron job doesn't seem to be working, check the log.

I've found four minutes to be a good interval. You don't want it running *too* often,
because it opens the "Now Playing" menu for an instant each time, which is mildly annoying if you're in the middle of typing.

Also, the more frequently the script runs, the faster the log will grow.
There isn't any rotation system in place (see [To do](#to-do)) so if you're concerned about losing a few megabytes of space, keep an eye on that file.

**If you use a different interval, you should change the status timeout in the code accordingly:**

```python
# Replace 5 with [your interval + 1]
resp = set_status(status, 'headphones', 5)
```

The timeout circumvents the need to ever clear the status:
if nothing is playing, the script does nothing, and Slack clears the status automatically.

### Blocklist

The blocklist is kept in `blocklist.txt` and it's really simple:
if any line in the text file matches (case-insensitive) a subphrase in the artist name or song title, the status is not updated.

### Substitutions

Substitutions are slightly more involved, but still pretty straightforward:
they're kept in a json file `substitutions.json`, where each key in the object is a (case-insensitive) search phrase
and the corresponding values are the text with which to substitute them.

Example:

substitutions.json:

```json
{
  "Foo": "Bar"
}
```

| Input | Output |
|---|---|
| Footloose - Kenny Loggins | Bartloose - Kenny Loggins |
| Everlong - Foo Fighters | Everlong - Bar Fighters |
| The Game Is Afoot - Daniel Pemberton | The Game Is ABart - Daniel Pemberton |

Notice the capitalization in the third example.

## Design

It reads both the Mac menu bar 'Now Playing' *and* the Youtube Music history for these reasons:

- Now Playing isn't necessarily music. It could be a video or, in some cases, the background sound of a webpage.
You probably don't want to set your status to those things.
- The YTM history doesn't say whether a track is currently playing, or even when it was played.
If you're not listening to anything, the latest entry in your history will stay the same.

We read the Mac 'Now Playing' value using Applescript because, as far as I know, that's the only way to do it,
short of distributing a signed Mac app to use system bindings.

The program is, ultimately, just a very rough script. It's not pretty, but it should be pretty easy to understand.
It's pretty easy to tell that I didn't originally intend to share it lol

## To do

- Extend the applescript snippet to read whether the Play or Pause button is visible in the Now Playing menu
  - This will solve the current problem of the program not being able to tell if you have YTM open but paused
- Accept status timeout as a command-line argument (see interval note under [Usage](#usage))
- Make it easier to connect to other streaming services, instead of YTM
- Add some kind of log rotation/truncation system so the log doesn't inflate indefinitely

## Development

There's not much to say. It's just a python script.

PRs are more than welcome.

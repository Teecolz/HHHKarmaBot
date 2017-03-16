"""
/r/hiphopheads Posting Bot
"""
# pylint: disable=E0712
import codecs
import time
import datetime as dt
import praw
import prawcore
import soundcloud
import tweepy
import handles
import keys


def main():
    """
    Run our loop to stay logged in and refreshing the subreddit.
    """
    subreddit = setup_connection_reddit('teecolz')

    auth = tweepy.OAuthHandler(keys.CONSUMER_KEY, keys.CONSUMER_SECRET)
    auth.set_access_token(keys.ACCESS_TOKEN, keys.ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    print "Signed in to Twitter"

    while 1:
        print '[bot] .................Scanning For New Tweets.................'
        tweet_scanner(api, subreddit)
        print '[sleep] .................Refreshing in 3 minutes.................'
        time.sleep(180)

def setup_connection_reddit(subreddit):
    """
    Log in to reddit
    """
    print "[bot] setting up connection with Reddit"
    red = praw.Reddit(client_id=keys.CLIENT_ID, client_secret=keys.CLIENT_SECRET,
                      password=keys.PASSWORD, user_agent=keys.USER_AGENT, username=keys.USERNAME)
    subreddit = red.subreddit(subreddit)
    print red.user.me()
    return subreddit

def check_if_new_soundcloud(subreddit, name, url):
    """
    sc
    """
    client = soundcloud.Client(client_id=keys.SOUNDCLOUD_CLIENT_ID)

    try:
        track = client.get('/resolve', url=url)
        posted_at = track.obj.get('created_at')[:19]
    except TypeError:
        print "--------------ERROR URL Is Invalid---------------"
        time.sleep(10)
    except client.HTTPError as err:
        print "--------------HTTP ERROR-----------------"
        print err
        time.sleep(60)

    current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime())

    # posted_at_time = posted_at[11:]
    # current_time_time = current_time[11:]

    start_dt = dt.datetime.strptime(posted_at, '%Y/%m/%d %H:%M:%S')
    end_dt = dt.datetime.strptime(current_time, '%Y/%m/%d %H:%M:%S')
    diff = (end_dt - start_dt)
    difference_in_minutes = diff.seconds/60

    try:
        posted_by = str(track.obj.get('user').get('username'))
        track_title = str(track.obj.get('title'))
    except UnicodeEncodeError as err:
        print err
        time.sleep(2)

    print "[info] Posted %s minutes ago (%s)" % (difference_in_minutes, posted_at)
    print "[info] Posted %s days ago" % diff.days
    print "[info] Current Time: %s " % current_time

    # hour_posted = posted_at_time[:2]
    # current_hour = current_time_time[:2]

    # if track was posted today and in last two hours
    if diff.days == 0 and difference_in_minutes < 120:
        print "[bot] FRESH TRACK: %s (%s) - %s" % (name, posted_by, track_title)
        post_to_reddit(subreddit, url, track, name)
    # elif hour_posted == 23:
    #     if posted_at[:7] == current_time[:7]:
    #         # if it just switched to the next day less than 2 hours ago...
    #         if current_hour == 00:
    #             if difference_in_minutes < 130:
    #                 print "FRESH TRACK: %s (%s) - %s" % (name, posted_by, track_title)
    #                 post_to_reddit(subreddit, url, track, name)
    #         elif current_hour == 01:
    #             if difference_in_minutes < 130:
    #                 print "FRESH TRACK: %s (%s) - %s" % (name, posted_by, track_title)
    #                 post_to_reddit(subreddit, url, track, name)


def post_to_reddit(subreddit, url, track, name):
    """
    handles posting to Reddit
    """
    try:
        submit = False
        same_artist = False
        add_artist_to_title = True
        soundcloud_username = str(track.obj.get('user').get('username'))
        track_title = str(track.obj.get('title'))

        if soundcloud_username[:4].lower() == name[:4].lower().strip(" "):
            same_artist = True
        elif soundcloud_username[:4].lower() in track_title.lower():
            add_artist_to_title = False
            same_artist = True
        elif name[:4].lower() in track_title.lower():
            add_artist_to_title = False
            same_artist = True

        if same_artist:
            if "-" in track_title and not add_artist_to_title:
                title = "[FRESH] " + track_title
            elif name.lower() in track_title.lower():
                title = "[FRESH] " + track_title
            else:
                if add_artist_to_title:
                    title = "[FRESH] " + name + " - " + track_title
            submit = True
        else:
            print "DIFFERENT ARTIST: " + soundcloud_username + " - " + track_title
            if "-" not in track_title:
                title = "[FRESH] " + soundcloud_username + " - " + track_title
            else:
                title = "[FRESH] " + track_title
            submit = True

        if submit:
            subreddit.submit(title, url=url, resubmit=False)
            print "[bot] POSTED: " + title + " >>> " + url + " by " + name


    except praw.exceptions.APIException as err:
        print "--------------REDDIT Praw API Erorr---------------"
        print err
        time.sleep(10)
    # pylint: disable=E0712
    except praw.exceptions as err:
        print "--------------REDDIT Praw ERROR---------------"
        print err
        time.sleep(30)
    except prawcore.PrawcoreException as err:
        print "--------------REDDIT Prawcore ERROR---------------"
        print err
        time.sleep(30)

# In this example, the handler is time.sleep(5 * 60),
# but you can of course handle it in any way you want.

def limit_handled(cursor):
    """
    Handles Twitter RateLimitError
    """
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print "Waiting..."
            time.sleep(5 * 60)
        # except StopIteration:
        #     break

def tweet_scanner(api, subreddit):
    """
    Handles all access to Twitter
    """
    for tweet in limit_handled(tweepy.Cursor(api.home_timeline).items(40)):
        screen_name = tweet.user.screen_name
        if is_song(tweet) and is_known_artist(screen_name):
            for name, handle in handles.HANDLES.iteritems():
                if str(screen_name).lower() == handle.strip("@").lower():
                    for link in tweet.entities['urls']:
                        expanded_link = link['expanded_url']
                        check_if_new_soundcloud(subreddit, name, expanded_link)

def is_song(tweet):
    """
    is it a song?
    """
    contains_song_link = False
    known_links = ['soundcloud'] # , 'youtu'
    if 'urls' in tweet.entities:
        for link in tweet.entities['urls']:
            expanded_link = link['expanded_url']
            if any(knownLink in expanded_link for knownLink in known_links):
                print "[link] " + expanded_link
                contains_song_link = True
                return contains_song_link

def is_known_artist(handle):
    """
    Checks if artist is in our Known Artists list
    """
    known = False

    # Scan through known twitter handles
    for key in handles.HANDLES:
        known_handle = handles.HANDLES.get(key).strip('@')
        if handle.lower() == known_handle.lower():
            print "[bot] Known Artist: " + handle
            known = True
    if not known:
        print "[bot] Unknown User: " + handle
    return known

if __name__ == '__main__':
    main()

import os
import random
import urllib
from datetime import datetime
from twython import Twython
from deta import App, Deta
from dotenv import load_dotenv
from fastapi import FastAPI
from io import BytesIO

load_dotenv('env')

app = App(FastAPI())
deta = Deta(os.environ.get('PROJECT_KEY'))
db = deta.Base('quotes')

def get_one_random_quote():
    # get quotes from deta base
    quotes = list(db.fetch({
        'posted_facebook_at': 'NULL',
        'posted_telegram_at': 'NULL',
        'posted_twitter_at': 'NULL',
    }))[0]
    # check at least one quote exists
    if quotes:
        return None
    # get one random quote
    return random.choice(quotes)

def format_quote_to_make_it_publishable(quote):
    return {
        'key': quote.get('key'),
        'text': quote.get('quote')+' --'+quote.get('by')
    }

def get_posting_type_by_current_date():
    day = int(datetime.now().strftime('%d'))
    return 'image' if (day % 5 == 0) else 'text'

def get_quote_image_url(formatted_quote):
    image_maker_url = os.environ.get('IMAGE_MAKER_URL')
    encoded_text = urllib.parse.quote(formatted_quote.get('text'))
    print(image_maker_url+'?text='+encoded_text)
    return image_maker_url+'?text='+encoded_text

def post_to_facebook(formatted_quote):
    print(formatted_quote)
    fb_id = os.environ.get('FACEBOOK_PAGE_ID')
    fb_token = os.environ.get('FACEBOOK_OAUTH_TOKEN')
    if formatted_quote.get('post_type') == 'image':
        fb_url = 'https://graph.facebook.com/'+fb_id+'/photos'
        fb_data = urllib.parse.urlencode({
            'url': formatted_quote.get('image_url'),
            'access_token': fb_token
        }).encode()
    else :
        fb_url = 'https://graph.facebook.com/'+fb_id+'/feed'
        fb_data = urllib.parse.urlencode({
            'message': formatted_quote.get('text'),
            'access_token': fb_token
        }).encode()
    try:
        urllib.request.urlopen(fb_url, fb_data)
        return True
    except:
        return False

def post_to_telegram(formatted_quote):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    channel = os.environ.get('TELEGRAM_CHANNEL')
    if formatted_quote.get('post_type') == 'image':
        tg_url =  'https://api.telegram.org/bot'+token+'/sendPhoto?'
        tg_url += 'photo=' + formatted_quote.get('image_url')
        tg_url += '&chat_id=' + channel
    else: # as text
        tg_url =  'https://api.telegram.org/bot'+token+'/sendMessage?'
        tg_url += 'text=' + urllib.parse.quote(formatted_quote.get('text'))
        tg_url += '&chat_id=' + channel
    try:
        urllib.request.urlopen(tg_url)
        return True
    except:
        return False

def post_to_twitter(formatted_quote):
    hastags = '\n\n#quotesindonesia #qotdindonesia #kutipan #motivasi #inspirasi'
    tw = Twython(
        os.environ.get('TWITTER_API_KEY'),
        os.environ.get('TWITTER_API_SECRET'),
        os.environ.get('TWITTER_OAUTH_TOKEN'),
        os.environ.get('TWITTER_OAUTH_SECRET')
    )
    try:
        if (formatted_quote.get('post_type') == 'image'):
            response = urllib.request.urlopen(formatted_quote.get('image_url'))
            image_io = BytesIO(response.read())
            tw_media = tw.upload_media(media=image_io)
            tw.update_status(media_ids=[tw_media['media_id']])
        else: # as text
            text_with_hastag = formatted_quote.get('text')+hastags
            tw.update_status(status=text_with_hastag[0:280])
        return True
    except:
        return False

def db_mark_quote_as_posted(formatted_quote):
    now = datetime.now().isoformat()
    db.update({
        'posted_facebook_at': now,
        'posted_telegram_at': now,
        'posted_twitter_at': now,
    }, formatted_quote.get('key'))

def get_formatted_quote_ready_to_post(quote):
    quote = get_one_random_quote()

    if quote is None:
        return None

    formatted_quote = format_quote_to_make_it_publishable(quote)
    post_type = get_posting_type_by_current_date()
    formatted_quote.update({'post_type': post_type})

    if post_type == 'image':
        formatted_quote.update({'image_url': get_quote_image_url(formatted_quote)})

    return formatted_quote

def post_to_social_media_and_update_quote(formatted_quote):
    fb = post_to_facebook(formatted_quote)
    tg = post_to_telegram(formatted_quote)
    tw = post_to_twitter(formatted_quote)
    if fb and tg and tw:
        db_mark_quote_as_posted(formatted_quote)
        return True
    return False

def autopost_to_social_medias():
    quote = get_one_random_quote()

    if quote is None:
        return {'success': False, 'message': 'No more quotes available.'}

    formatted_quote = format_quote_to_make_it_publishable(quote)
    post_type = get_posting_type_by_current_date()
    formatted_quote.update({'post_type': post_type})

    if post_type == 'image':
        formatted_quote.update({'image_url': get_quote_image_url(formatted_quote)})

    fb = post_to_facebook(formatted_quote)
    tg = post_to_telegram(formatted_quote)
    tw = post_to_twitter(formatted_quote)

    if fb and tg and tw:
        return  {'sucess': True, 'message': '✔ all clear'}
    else:
        return {'success': False, 'message': 'Oops, Something went wrong!'}

@app.route('/')
def http_index():
    return 'HTTP 200 OK'

@app.route('/4e24e9ce55acaf0b6b4e9b0a3133182d')
def http_autopost():
    return autopost_to_social_medias()

@app.lib.run(action='autopost')
@app.lib.cron()
def run_autopost(event):
    return autopost_to_social_medias()

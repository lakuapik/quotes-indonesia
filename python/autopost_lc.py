#!/usr/bin/env python3

'''
This script run on local
'''

import os
import random
import urllib
import shutil
import tempfile
from io import BytesIO
from flask import Flask, abort
from twython import Twython
from datetime import datetime
from google.cloud import firestore

import dotenv
dotenv.load_dotenv('autopost.env')

credential = os.environ['CREDENTIAL']
tg_token = os.environ['TG_TOKEN']
tg_channel = os.environ['TG_CHANNEL']
tg_me_id = os.environ['TG_ME_ID']
fb_token = os.environ['FB_TOKEN']
fb_id = os.environ['FB_ID']
tw_api_key = os.environ['TW_API_KEY']
tw_api_secret = os.environ['TW_API_SECRET']
tw_oa_token = os.environ['TW_OA_TOKEN']
tw_oa_secret = os.environ['TW_OA_SECRET']
image_maker_url = os.environ['IMAGE_MAKER_URL']

app = Flask(__name__)

@app.route('/')
def qi_autopost():
    # INIT DATABASE

    # save credential
    fd, service_account_file = tempfile.mkstemp()
    os.write(fd, credential.encode())
    os.close(fd)

    # init firestore client with custom json credential
    db = firestore.Client.from_service_account_json(service_account_file)

    # GET RANDOM QUOTE

    # db collection and query
    qi_ref = db.collection('quotes_indonesia')
    quotes = qi_ref.where('posted_fb', '==', False).where('posted_tg', '==', False).stream()

    # parsing to array of dict
    parsed_quotes = []
    for quote in quotes:
        qx = quote.to_dict()
        qx['id'] = quote.id
        parsed_quotes.append(qx)

    # check at least one quote exists
    if (len(parsed_quotes) == 0):
        print('No quote available.')
        abort(204)

    # get one random quote
    selected_quote = random.choice(parsed_quotes)
    selected_quote_formatted = selected_quote['quote']+' --'+selected_quote['by']
    selected_quote_with_hastag = selected_quote_formatted + '\n\n#quotesindonesia #qotdindonesia #kutipan #motivasi #inspirasi'

    # POSTING

    # Post as text or image
    current_date = int(datetime.now().strftime('%d'))
    image_url = image_maker_url+'?text='
    image_url += urllib.parse.quote(selected_quote_formatted)
    if (current_date % 5 == 0): # as image
        # save image in memory
        image_io = BytesIO(urllib.request.urlopen(image_url).read())
        # telegram
        tg_url =  'https://api.telegram.org/bot'+tg_token+'/sendPhoto?'
        tg_url += 'photo=' + image_url
        tg_url += '&chat_id=' + tg_channel
        # facebook
        fb_url = 'https://graph.facebook.com/'+fb_id+'/photos'
        fb_data = urllib.parse.urlencode({
            'url': image_url,
            'access_token': fb_token
        }).encode()
    else : # as text
        # telegram
        tg_url =  'https://api.telegram.org/bot'+tg_token+'/sendMessage?'
        tg_url += 'text=' + urllib.parse.quote(selected_quote_formatted)
        tg_url += '&chat_id=' + tg_channel
        # facebook
        fb_url = 'https://graph.facebook.com/'+fb_id+'/feed'
        fb_data = urllib.parse.urlencode({
            'message': selected_quote_formatted,
            'access_token': fb_token
        }).encode()

    # Send it!
    # Telegram
    try:
        # hit api
        urllib.request.urlopen(tg_url)
        # updating posted attribute
        qi_ref.document(selected_quote['id']).set({
            'posted_tg': True,
        }, merge=True)
    except:
        print('Failed to post telegram.')
    # Facebook
    try:
        # hit api
        urllib.request.urlopen(fb_url, fb_data)
        # updating posted attribute
        qi_ref.document(selected_quote['id']).set({
            'posted_fb': True,
        }, merge=True)
    except:
        print('Failed to post facebook.')
    # Twitter
    try:
        # hit api
        tw = Twython(tw_api_key, tw_api_secret, tw_oa_token, tw_oa_secret)
        if (current_date % 5 == 0): # as image
            tw_media = tw.upload_media(media=image_io)
            tw.update_status(media_ids=[tw_media['media_id']])
        else: # as text
            tw.update_status(status=selected_quote_with_hastag[0:280])
        # updating posted attribute
        qi_ref.document(selected_quote['id']).set({
            'posted_tw': True,
        }, merge=True)
    except:
        print('Failed to post twitter.')
    # My Bot
    try:
        # telegram post data
        re_url =  'https://api.telegram.org/bot'+tg_token+'/sendPhoto?'
        re_url += 'photo=' + image_url
        re_url += '&chat_id='+os.environ['TG_ME_ID']
        urllib.request.urlopen(re_url)
    except:
        print('Failed to post to bot.')

    return 'OK'

if __name__ == "__main__":
    app.run(debug=True)

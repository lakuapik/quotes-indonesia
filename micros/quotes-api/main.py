import json
import os
import random
from deta import App, Deta
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv('env')

app = App(FastAPI())
deta = Deta(os.environ.get('PROJECT_KEY'))
db = deta.Base('quotes')

db_appends = {
    'posted_facebook_at': 'NULL',
    'posted_telegram_at': 'NULL',
    'posted_twitter_at': 'NULL',
}

def db_get_quotes(query):
    return list(db.fetch(query))[0]

def db_cleanup_quotes(quotes):
    for quote in quotes:
        for k in db_appends.keys():
            quote.pop(k, None)
    return quotes

@app.get('/')
def http_index():
    quotes = db_get_quotes({})
    return db_cleanup_quotes(quotes)

@app.get('/random')
def http_random():
    query = db_appends
    quotes = db_get_quotes(query)
    quotes = db_cleanup_quotes(quotes)
    return random.choice(quotes)

@app.lib.run(action='refresh-database')
def run_refresh_database(event):
    # delete old data
    # TODO: find a method drop database
    for quote in db_get_quotes({}):
        db.delete(quote.get('key'))
    # insert new ones
    with open('quotes.min.json') as file:
        quotes = json.load(file)
        for quote in quotes:
            quote.update(db_appends)
            db.put(quote)
    return "✔ success"

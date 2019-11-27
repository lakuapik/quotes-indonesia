#!/usr/bin/env python3

import os
import csv
import json
import operator
import tempfile
from flask import Flask, jsonify
from google.cloud import firestore

import dotenv
dotenv.load_dotenv('parser.env')

credential = os.environ['CREDENTIAL']

app = Flask(__name__)

@app.route('/')
def parser():
    # INIT DATABASE

    # save credential
    fd, service_account_file = tempfile.mkstemp()
    os.write(fd, credential.encode())
    os.close(fd)

    # init firestore client with custom json credential
    db = firestore.Client.from_service_account_json(service_account_file)

    # GET QUOTES

    # db collection and query
    quotes_col = db.collection('quotes_indonesia').stream()

    # parsing to array of dict
    quotes = []
    for quote in quotes_col:
        qx = quote.to_dict()
        quotes.append({
            'by': qx.get('by'),
            'quote': qx.get('quote')
        })

    # sort by
    quotes.sort(key=operator.itemgetter('by'))
    
    # save to quotes.json
    with open('./../raw/quotes.json', 'w') as f:
        f.write(json.dumps(quotes, indent=4, sort_keys=True))

    # save to quotes.min.json
    with open('./../raw/quotes.min.json', 'w') as f:
        f.write(json.dumps(quotes, sort_keys=True))

    # save to quotes.csv
    with open('./../raw/quotes.csv', 'w') as f:
        writer = csv.writer(f)
        row = 0
        for quote in quotes:
            if row == 0:
                header = quote.keys()
                writer.writerow(header)
                row += 1
            writer.writerow(quote.values())

    return jsonify(quotes)

if __name__ == "__main__":
    app.run(debug=True)

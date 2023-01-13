from flask import Flask, request, jsonify
from puppy import pup

app = Flask(__name__)

@app.route('/fetch', methods=['POST'])
def fetch():
    data = request.json
    return jsonify(data)

app.run()

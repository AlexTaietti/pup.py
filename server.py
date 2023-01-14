from flask import Flask, request
from puppy import pup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/fetch', methods=['POST'])
def fetch():
    data = request.json
    start = data["start"]
    target = data["target"]
    pupper = pup.Puppy(start, target)
    result = pupper.run()
    return result

app.run()

import os
import random
import numpy
import logging
import sys

from flask_cors import cross_origin


import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

from PIL import Image
from grpc.beta import implementations
from mnist import MNIST
from flask import Flask, render_template, request, jsonify


app = Flask(__name__, static_url_path='/static', static_folder='static')
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

F_MODEL_SERVER_HOST = os.getenv("TF_MODEL_SERVER_HOST", "127.0.0.1")
TF_MODEL_SERVER_PORT = int(os.getenv("TF_MODEL_SERVER_PORT", 9000))

@app.route("/")
def main():
    return render_template('main.html')

@app.route('/predict', methods=['POST', 'OPTIONS'])
@cross_origin()
def predict():

    from flask import request
    if request.method == "POST" or request.method == "OPTIONS":
        # get url
        data = request.get_json(force=True)
        zVector = data.get('zVector')
        if not zVector:
            return jsonify(
                data='error'
            )
    return "1"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)

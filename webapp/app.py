import os
import logging
import sys


from flask_cors import cross_origin
from io import BytesIO


import tensorflow as tf
import numpy as np
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2
import base64
from PIL import Image
from grpc.beta import implementations
from flask import Flask, render_template, request, jsonify


app = Flask(__name__, static_url_path='/static', static_folder='static')
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

TF_MODEL_SERVER_HOST = os.getenv("TF_MODEL_SERVER_HOST", "127.0.0.1")
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

        # from notebook

        zVector = list(map(float, zVector))
        # zVector = np.random.uniform(-1, 1, size=(1, 100))
        channel = implementations.insecure_channel(TF_MODEL_SERVER_HOST, int(TF_MODEL_SERVER_PORT))
        stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

        request = predict_pb2.PredictRequest()
        request.model_spec.name = 'mnist'
        request.model_spec.signature_name = 'generated'
        request.inputs['zVector'].CopyFrom(
            tf.contrib.util.make_tensor_proto(zVector, dtype=tf.float32, shape=(1, 100)))
        result_future = stub.Predict(request, 30)

        image = np.asarray(result_future.outputs['image'].float_val)

        mat = np.reshape(image, (28, 28))
        img = Image.fromarray(np.uint8(mat * 255), 'L')

        size = 28 * 28
        # string = ''
        # strings = []
        # for i in range(0, size):
        #     if (i + 1) % 28 == 0:
        #         strings.append(string)
        #         string = ''
        #     else:
        #         string += '*' if image[i] < 0 else 'O'
        output = BytesIO()
        img.save(output, format='JPEG')
        im_data = output.getvalue()

        return jsonify(image='data:image/jpg;base64,' + base64.b64encode(im_data).decode())

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)

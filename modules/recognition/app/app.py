import json
import os
import io
import sys

# Imports for the REST API
from flask import Flask, request

# Imports for prediction
from predict import predict_image
from process_feature import FeatureProcessor

app = Flask(__name__)

# Default route just shows simple text
@app.route('/')
def index():
    return 'Recognition model host harness'

# Like the CustomVision.ai Prediction service /image route handles either
#     - octet-stream image file 
#     - a multipart/form-data with files in the imageData parameter
@app.route('/send/<role>', methods=['POST'])
def predict_image_handler(role):
    try:
        imageData = io.BytesIO(request.get_data())
        result = predict_image(imageData, role)
    
        return json.dumps(result)

    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500

@app.route('/save/<id>', methods=['POST'])
def save_feature_data(id):
    try:
        processor = FeatureProcessor(file_name="feature_temp.csv", command="save", transaction_id=id)
        processor.start()
        return "OK"
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500

if __name__ == '__main__':
    # Load and intialize the model
    print("Start flask.")

    # Run the server
    app.run(host='0.0.0.0', port=80)


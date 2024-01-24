from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

result_file = 'prediction_result.json'

prediction_threshold = 0.90

def make_prediction(image_file):
    prediction_key = "27dea928805b4e6baf8b46e2854986b7"
    endpoint = 'https://cvobjectdetector-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/060c28e6-5b5f-41cb-8426-5036e6cfa1b9/detect/iterations/Iteration1/image'
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }
    response = requests.post(endpoint, headers=headers, data=image_file.read())

    if response.status_code == 200:
        result = response.json()
        return {
            "Total Ribbons": sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Ribbon" and obj["probability"] >= prediction_threshold),
            "Total Arrows": sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Arrow" and obj["probability"] >= prediction_threshold),
            "Total Stars": sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Star" and obj["probability"] >= prediction_threshold)
        }
    else:
        return {"Error": f"{response.status_code} - {response.text}"}

def update_result_file(prediction_result):
    global result_file  # Declare result_file as a global variable

    # Create a new result file with the current prediction results
    with open(result_file, 'w') as result_file:
        json.dump(prediction_result, result_file)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            if 'image' not in request.files:
                return jsonify({"Error": "No image file provided"}), 400

            image_file = request.files['image']

            if image_file.filename == '':
                return jsonify({"Error": "No selected file"}), 400

            # Make predictions
            prediction_result = make_prediction(image_file)

            # Update the result file with the new prediction results
            update_result_file(prediction_result)

            # Return a response indicating successful image processing
            return jsonify({"Message": "Image processed successfully"})
        except Exception as e:
            return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500

    elif request.method == 'GET':
        # HTML form directly defined within the Python script
        return '''
        <!doctype html>
        <title>Upload an image</title>
        <h1>Upload an image</h1>
        <form method=post enctype=multipart/form-data>
            <input type=file name=image>
            <input type=submit value=Upload>
        </form>
        '''

@app.route('/result', methods=['GET'])
def retrieve_result():
    try:
        result_file_path = 'prediction_result.json'  # Specify the path to the result file

        # Read the latest result from the file
        if os.path.exists(result_file_path) and os.path.getsize(result_file_path) > 0:
            with open(result_file_path, 'r') as result_file:
                result = json.load(result_file)

            return jsonify(result)
        else:
            return jsonify({"Error": "Result file is empty"}), 500
    except FileNotFoundError:
        return jsonify({"Error": "Result file not found"}), 500
    except Exception as e:
        return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)


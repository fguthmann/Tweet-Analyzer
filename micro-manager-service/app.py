import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

@app.route('/handle-request', methods=['POST'])
def handle_requests():
    data = request.json
    app.logger.info(data)

    try:
        # Forward the request to the token-finding-service
        response = requests.post('http://token-finding-service:3003/find-tweets', json=data)
        if response.status_code != 200:
            return jsonify({"error": "Failed to communicate with token-finding-service", "status_code": response.status_code}), response.status_code
        app.logger.info(response.json())

        # Forward the response to the tweet-analyzing-service
        response = requests.post('http://tweet-analyzing-service:3004/analyze-tweets', json=response.json())
        if response.status_code != 200:
            return jsonify({"error": "Failed to communicate with tweet-analyzing-service", "status_code": response.status_code}), response.status_code
        app.logger.info(response.json())

        # Forward the response to the analysis-visualizer-service
        response = requests.post('http://analysis-visualizer-service:3005/visualize', json=response.json())
        if response.status_code == 200:
            # Directly pass through the HTML response
            return Response(response.content, mimetype='text/html')
        else:
            return jsonify({"error": "Failed to communicate with analysis-visualizer-service", "status_code": response.status_code}), response.status_code

    except requests.exceptions.RequestException as e:
        print(e)
        return jsonify({"error": "Network error occurred"}), 500

@app.route('/')
def hello():
    return "Hello, I am the manager and I am up and running"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3010)
    
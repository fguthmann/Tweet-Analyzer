import os
from flask import Flask, request, jsonify
import tweepy

app = Flask(__name__)


api_key = os.getenv('TWITTER_API_KEY')
api_secret_key = os.getenv('TWITTER_API_SECRET_KEY')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')


def connect_to_api():
    auth = tweepy.OAuthHandler(api_key, api_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


@app.route('/post-tweet', methods=['POST'])
def post_tweet():
    api = connect_to_api()
    data = request.get_json()
    status = data.get("status")

    if not status:
        return jsonify({"error": "Status is required"}), 400

    try:
        tweet = api.update_status(status=status)
        return jsonify({"message": "Tweet posted successfully", "tweet_id": tweet.id_str}), 200
    except Exception as e:
        return jsonify({"error": "Failed to post tweet", "details": str(e)}), 500


@app.route('/')
def hello():
    return "Hello, upload is ready now!"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3020)
    
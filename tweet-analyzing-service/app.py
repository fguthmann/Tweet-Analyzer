import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Database connection details from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")


def connect_to_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST
    )
    return conn


def get_tweet_from_db(tweet_id, cur):
    # Function to retrieve a tweet from the database by ID
    cur.execute("SELECT * FROM tweets WHERE unique_id = %s", (tweet_id,))
    tweet = cur.fetchone()
    return tweet


@app.route('/analyze-tweets', methods=['POST'])
def analyze_tweets():
    data = request.json
    insights = {}
    conn = None
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        for token, tweet_ids in data.items():
            tweets = {}
            current_tweets = []
            for tweet_id in tweet_ids:
                if tweet_id not in tweets:
                    tweet = get_tweet_from_db(tweet_id, cursor)
                    if tweet:
                        tweet_dict = {
                            "unique_id": tweet[0],
                            "author": tweet[1],
                            "content": tweet[2],
                            "country": tweet[3],
                            "date_time": tweet[4],
                            "id": tweet[5],
                            "language": tweet[6],
                            "latitude": tweet[7],
                            "longitude": tweet[8],
                            "number_of_likes": tweet[9],
                            "number_of_shares": tweet[10]
                        }
                        tweets[tweet_id] = tweet_dict
                        current_tweets.append(tweet_dict)
                else:
                    current_tweets.append(tweets[tweet_id])
                    
            app.logger.info("Starting to analyze " + token)
            total_tweets = len(current_tweets)

            # Tweet with the highest number of likes and average number of likes
            max_likes = max(current_tweets, key=lambda x: x['number_of_likes'])
            avg_likes = sum(tweet['number_of_likes'] for tweet in current_tweets) / total_tweets

            # Tweet with the highest number of shares and average number of shares
            max_shares = max(current_tweets, key=lambda x: x['number_of_shares'])
            avg_shares = sum(tweet['number_of_shares'] for tweet in current_tweets) / total_tweets

            # Compile insights for the token
            insights[token] = {
                "total_number_of_tweets": total_tweets,
                "tweet_with_highest_number_of_likes": max_likes['unique_id'],
                "average_number_of_likes": avg_likes,
                "tweet_with_highest_number_of_shares": max_shares['unique_id'],
                "average_number_of_shares": avg_shares,
                "tweet_datetimes": [tweet['date_time'] for tweet in current_tweets]
            }

            current_tweets.clear()

        return jsonify(insights)
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"error": "Internal server error", "details": str(error)}), 500
    finally:
        if conn is not None:
            conn.close()


@app.route('/')
def hello():
    return "Hello, I am up and running, I am the analyzer"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3004)
    
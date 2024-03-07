import os
from datetime import datetime
import psycopg2
import csv
from flask import Flask, request, jsonify
import tweepy

app = Flask(__name__)

# Database connection details from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")

api_key = os.getenv('TWITTER_API_KEY')
api_secret_key = os.getenv('TWITTER_API_SECRET_KEY')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')


def connect_to_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST
    )
    return conn


def connect_to_api():
    auth = tweepy.OAuthHandler(api_key, api_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


def create_tables():
    commands = (
        """
                CREATE TABLE IF NOT EXISTS tweets (
                unique_id SERIAL PRIMARY KEY,
                author VARCHAR(255),
                content TEXT,
                country VARCHAR(255), -- Nullable column
                date_time TIMESTAMP WITHOUT TIME ZONE,
                id TEXT,
                language VARCHAR(50),
                latitude NUMERIC(10, 8), -- Nullable column
                longitude NUMERIC(11, 8), -- Nullable column
                number_of_likes INT,
                number_of_shares INT
                )
                """
    )
    conn = None
    try:
        # Connect to the database
        conn = connect_to_db()
        cur = conn.cursor()
        # Create table one by one
        for command in commands:
            cur.execute(command)
        # Close communication with the database
        cur.close()
        # Commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def load_csv_into_db(file_path):
    insert_sql = """
    INSERT INTO tweets(author, content, country, date_time, id, language, latitude, longitude, number_of_likes, number_of_shares)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = None
    try:
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tweets")
        row_count = cursor.fetchone()[0]
        if row_count != 0:
            return 
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # Skip the header
            rows = []
            for row in csv_reader:
                # Convert empty strings to None for numeric fields
                row = [None if col == '' else col for col in row]
                row[3] = parse_date(row[3])
                rows.append(tuple(row))
    
        try:
            cursor.executemany(insert_sql, rows)
            conn.commit()
        except psycopg2.DatabaseError as e:
            conn.rollback()
        finally:
            cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


@app.before_first_request
def startup():
    # Create tables if they don't exist
    create_tables()
    # Load CSV data into the database
    load_csv_into_db("tweets.csv")


@app.route('/')
def hello():
    return "Hello, the tables should be set up now!"


@app.route('/grab-tweets', methods=['POST'])
def grab_tweets_from_api():
    tokens = request.json['tokens']
    api = connect_to_api()
    search_query = " ".join(tokens)

    try:
        # Fetch tweets
        tweets = api.search(q=search_query, count=100)  # Adjust count as needed

        # Process and insert tweets into the database
        for tweet in tweets:
            # Extract required fields from each tweet
            author = tweet.user.screen_name
            content = tweet.text
            country = None  # This might require additional logic based on tweet.place
            date_time = tweet.created_at
            tweet_id = tweet.id_str
            language = tweet.lang
            latitude = None if tweet.coordinates is None else tweet.coordinates['coordinates'][1]
            longitude = None if tweet.coordinates is None else tweet.coordinates['coordinates'][0]
            number_of_likes = tweet.favorite_count
            number_of_shares = tweet.retweet_count

            # Prepare data for insertion
            tweet_data = (author, content, country, date_time, tweet_id, language, latitude, longitude, number_of_likes, number_of_shares)

            # Insert tweet into database (simplified version)
            insert_sql = """
            INSERT INTO tweets(author, content, country, date_time, id, language, latitude, longitude, number_of_likes, number_of_shares)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            conn = connect_to_db()
            cursor = conn.cursor()
            try:
                cursor.execute(insert_sql, tweet_data)
                conn.commit()
            except psycopg2.DatabaseError as e:
                conn.rollback()
                print(e)
            finally:
                cursor.close()
                conn.close()

        return jsonify({"message": "Tweets fetched and inserted successfully."}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to fetch or insert tweets"}), 500


# Function to parse and convert date/time format
def parse_date(date_str):
    try:
        # Assuming the date/time format is 'DD/MM/YYYY HH:MM'
        dt_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
        return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("Error: Invalid date/time format")
        return None
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3999)
    
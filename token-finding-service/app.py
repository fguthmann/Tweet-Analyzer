import os
import psycopg2
import itertools
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


@app.route('/find-tweets', methods=['POST'])
def find_tweets():
    retrieved_tweets = {}
    tokens = request.json['tokens']
    conn = None
    try:
        # Connect to the database
        conn = connect_to_db()
        cursor = conn.cursor()
        
        for r in range(1, len(tokens) + 1):
            for subset in itertools.combinations(tokens, r):
                app.logger.info(subset)
                subset_key = " ".join(subset)
                # Modified query to exclude tweets with author 'None'
                query = "SELECT unique_id FROM tweets WHERE " + \
                        " AND ".join(["content ILIKE %s" for _ in subset]) + \
                        " AND author <> 'None'"
                cursor.execute(query, tuple(f"%{token}%" for token in subset))
                result = cursor.fetchall()

                if not result:  # If no tweets found, try fetching a tweet with author 'None'
                    fallback_query = "SELECT unique_id FROM tweets WHERE " + \
                                     "author = 'None'"
                    cursor.execute(fallback_query, tuple(f"%{token}%" for token in subset))
                    result = cursor.fetchall()
    
                app.logger.info(result)

                flat_result = [item[0] for item in result]
                
                app.logger.info(flat_result)

                retrieved_tweets[subset_key] = flat_result
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"error": str(error)}), 500
    finally:
        if conn is not None:
            conn.close()
            
    return jsonify(retrieved_tweets)


@app.route('/')
def hello():
    return "Hello, I am up and running"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3003)
    
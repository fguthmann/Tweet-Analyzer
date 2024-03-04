import base64
import os
from datetime import datetime
from io import BytesIO

import pandas as pd
import psycopg2
from flask import Flask, request
from matplotlib import pyplot as plt

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


@app.route('/visualize', methods=['POST'])
def visualize_analysis():
    data = request.json
    df = pd.DataFrame(data).T  # Transpose to get tokens as rows
    df['token'] = df.index
    df['tweet_datetimes'] = df['tweet_datetimes'].apply(lambda x: [datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z") for date in x])
    most_popular_tweet = grab_most_popular_tweet(df)
    bar_graphs = generate_bar_graphs(df)
    line_charts = generate_line_charts(df)
    scatter_plot = generate_scatter_plot(df)
    return generate_web_page(most_popular_tweet, bar_graphs, line_charts, scatter_plot)


def grab_most_popular_tweet(df):
    try:
        most_popular_tweet = None
        
        conn = connect_to_db()
        cursor = conn.cursor()

        tweets_cache = {}  # Cache to avoid fetching the same tweet multiple times
        popular_tweets = {}

        for index, row in df.iterrows():
            for metric in ["likes", "shares"]:
                # Determine the right column index based on the metric
                tweet_id = row["tweet_with_highest_number_of_" + metric]

                if tweet_id not in tweets_cache:
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
                        tweets_cache[tweet_id] = tweet_dict  # Cache this tweet
                        popular_tweets[row["token"] + " " + metric] = tweet_dict
                else:
                    # If the tweet is already in cache, use it
                    popular_tweets[row["token"] + " " + metric] = tweets_cache[tweet_id]

        highest_popularity_score = -1  # Sum of likes and shares

        # Iterate over each tweet in the popular_tweets dictionary
        for tweet_id, tweet_data in popular_tweets.items():
            # Calculate the sum of likes and shares for the current tweet
            popularity_score = tweet_data['number_of_likes'] + tweet_data['number_of_shares']

            # Update the most popular tweet if the current tweet has a higher score
            if popularity_score > highest_popularity_score:
                most_popular_tweet = tweet_data
                highest_popularity_score = popularity_score
        return most_popular_tweet
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    
    
def generate_bar_graphs(df):
    images = []  # To store images
    token_lengths = df['token'].apply(lambda x: len(x.split()))
    unique_lengths = sorted(token_lengths.unique())

    if len(unique_lengths) == 1:  # If there's only one unique token length
        length = unique_lengths[0]
        subset_df = df[token_lengths == length]
        title = f'Total Tweets for Tokens with Exactly {length} Words'
        fig, ax = plt.subplots()
        subset_df.plot(kind='bar', x='token', y='total_number_of_tweets', title=title, ax=ax)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)  # Set labels rotation to horizontal
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        images.append(buf.getvalue())
    else:
        for i, length in enumerate(unique_lengths[:-1]):  # Exclude the last length initially
            if i == len(unique_lengths) - 2:  # If this is the second to last length, include the last length as well
                subset_df = df[token_lengths >= length]
                title = f'Total Tweets for Tokens with {length} or More Words'
            else:
                subset_df = df[token_lengths == length]
                title = f'Total Tweets for Tokens with Exactly {length} Words'
            fig, ax = plt.subplots()
            subset_df.plot(kind='bar', x='token', y='total_number_of_tweets', title=title, ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0)  # Set labels rotation to horizontal
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close(fig)
            images.append(buf.getvalue())

    return images


def generate_line_charts(df):
    images = []  # To store images
    df['token_length'] = df['token'].apply(lambda x: len(x.split()))
    unique_lengths = sorted(df['token_length'].unique())

    if len(unique_lengths) == 1:  # If there's only one unique token length
        length = unique_lengths[0]
        tokens_df = df[df['token_length'] == length]
        title = f'Tweets Over Time for Tokens with Exactly {length} Words'
        fig, ax = plt.subplots()
        for token in tokens_df['token'].unique():
            token_df = tokens_df[tokens_df['token'] == token]
            dates_df = pd.DataFrame(token_df['tweet_datetimes'].iloc[0], columns=['datetime'])
            dates_df['count'] = 1
            dates_df.set_index('datetime', inplace=True)
            counts = dates_df.resample('M').sum()['count']
            ax.plot(counts.index, counts.values, label=token)  # Plot with ax.plot for better control
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Tweets')
        ax.legend()
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        images.append(buf.getvalue())
    else:
        for i, length in enumerate(unique_lengths[:-1]):  # Exclude the last length initially
            if i == len(unique_lengths) - 2:  # Check if it's the second to last length
                tokens_df = df[df['token_length'] >= length]
                title = f'Tweets Over Time for Tokens with {length} or More Words'
            else:
                tokens_df = df[df['token_length'] == length]
                title = f'Tweets Over Time for Tokens with Exactly {length} Words'

            if not tokens_df.empty:
                fig, ax = plt.subplots()
                for token in tokens_df['token'].unique():
                    token_df = tokens_df[tokens_df['token'] == token]
                    dates_df = pd.DataFrame(token_df['tweet_datetimes'].iloc[0], columns=['datetime'])
                    dates_df['count'] = 1
                    dates_df.set_index('datetime', inplace=True)
                    counts = dates_df.resample('M').sum()['count']

                    ax.plot(counts.index, counts.values, label=token)  # Use ax.plot() for better control

                ax.set_title(title)
                ax.set_xlabel('Date')
                ax.set_ylabel('Number of Tweets')
                ax.legend()

                buf = BytesIO()
                plt.savefig(buf, format='png')
                plt.close(fig)
                images.append(buf.getvalue())

    return images


def generate_scatter_plot(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    for index, row in df.iterrows():
        ax.scatter(row['average_number_of_likes'], row['average_number_of_shares'], label=index)
    ax.set_xlabel('Average Number of Likes')
    ax.set_ylabel('Average Number of Shares')
    ax.legend()
    ax.set_title('Average Likes vs. Shares for Each Token')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()


def generate_web_page(most_popular_tweet, bar_graphs, line_charts, scatter_plot):
    bar_graphs_base64 = [convert_image_to_base64(img) for img in bar_graphs]
    line_charts_base64 = [convert_image_to_base64(img) for img in line_charts]
    scatter_plot_base64 = convert_image_to_base64(scatter_plot)

    # Generate HTML content
    html_content = """
<html>
<head>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
<style>
    .carousel-control-prev-icon,
    .carousel-control-next-icon {
        filter: invert(100%);
    }
</style>
</head>
<body>
<h1>Visualization Analysis</h1>
"""

    if most_popular_tweet:
        html_content += f"<h2>Most Popular Tweet</h2>"
        html_content += f"<p>Author: {most_popular_tweet['author']}</p>"
        html_content += f"<p>Content: {most_popular_tweet['content']}</p>"
        html_content += f"<p>Likes: {most_popular_tweet['number_of_likes']}, Shares: {most_popular_tweet['number_of_shares']}</p>"

    if bar_graphs_base64:
        html_content += """
    <div id="barGraphCarousel" class="carousel slide" data-ride="carousel">
        <div class="carousel-inner">
    """

    for idx, img in enumerate(bar_graphs_base64):
        if idx == 0:
            html_content += f'<div class="carousel-item active"><img src="data:image/png;base64,{img}" class="d-block w-100"></div>'
        else:
            html_content += f'<div class="carousel-item"><img src="data:image/png;base64,{img}" class="d-block w-100"></div>'

    html_content += """
        </div>
        <a class="carousel-control-prev" href="#barGraphCarousel" role="button" data-slide="prev">
            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
            <span class="sr-only">Previous</span>
        </a>
        <a class="carousel-control-next" href="#barGraphCarousel" role="button" data-slide="next">
            <span class="carousel-control-next-icon" aria-hidden="true"></span>
            <span class="sr-only">Next</span>
        </a>
    </div>
    """

    if line_charts_base64:
        html_content += """
    <div id="lineChartCarousel" class="carousel slide" data-ride="carousel">
        <div class="carousel-inner">
    """

    for idx, img in enumerate(line_charts_base64):
        if idx == 0:
            html_content += f'<div class="carousel-item active"><img src="data:image/png;base64,{img}" class="d-block w-100"></div>'
        else:
            html_content += f'<div class="carousel-item"><img src="data:image/png;base64,{img}" class="d-block w-100"></div>'

    html_content += """
        </div>
        <a class="carousel-control-prev" href="#lineChartCarousel" role="button" data-slide="prev">
            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
            <span class="sr-only">Previous</span>
        </a>
        <a class="carousel-control-next" href="#lineChartCarousel" role="button" data-slide="next">
            <span class="carousel-control-next-icon" aria-hidden="true"></span>
            <span class="sr-only">Next</span>
        </a>
    </div>
    """
    
    html_content += "<h2>Scatter Plot</h2>"
    html_content += f'<img src="data:image/png;base64,{scatter_plot_base64}">'

    html_content += """
<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
"""
    html_content += "</body></html>"

    return html_content


def convert_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')


@app.route('/')
def hello():
    return "Hello, I am up and running, I am the visualizer"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3005)
    
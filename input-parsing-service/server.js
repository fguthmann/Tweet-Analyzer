const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3002;

// Middleware to parse request bodies
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

app.post('/parse-input', async (req, res) => {
    const { tokens, source } = req.body;

    // Example of parsing input. You might need to adjust based on actual input format.
    const parsedTokens = tokens.split(/\s+|[,.;!?\\:]+/).filter(Boolean); // Assuming tokens are sent as a space-separated string

    try {
        await axios.get('http://database-feeding-service:3999/'); // Adjust the URL to your Flask service
        console.log('The database now contains tweets.csv');
    } catch (error) {
        console.error('Error initializing Flask service:', error);
        return res.status(500).json({ message: 'Failed to initialize Flask service', error: error.message });
    }
    
    if (source === 'Upload tweet') {
        console.log('Uploading input as tweet.');
        try {
            // Assuming the tweet-uploading-service is running and accessible at this URL
            // and it expects a POST request with a JSON body containing a "status" field
            const tweetResponse = await axios.post('http://tweet-uploading-service:3020/post-tweet', {
                status: tokens // Assuming the entire tokens string is the tweet text
            });

            // Check the response from tweet-uploading-service
            if (tweetResponse.status === 200) {
                console.log('Tweet uploaded successfully:', tweetResponse.data);
                return res.status(200).json({ message: 'Tweet uploaded successfully', details: tweetResponse.data });
            } else {
                console.log('Failed to upload tweet:', tweetResponse.data);
                return res.status(tweetResponse.status).json({ message: 'Failed to upload tweet', error: tweetResponse.data });
            }
        } catch (error) {
            console.error('Error uploading tweet:', error);
            return res.status(500).json({ message: 'Failed to upload tweet', error: error.message });
        }
    }


    if (source === 'API') {
        console.log('Fetching from Twitter API via Flask microservice');
        /* Commented out because Twitter API v1.1 for tweet grabbing is no longer freely available...
        try {
            // Here we make a POST request to the grab_tweets endpoint with the parsed tokens
            const response = await axios.post('http://database-feeding-service:3999/grab-tweets', {
                tokens: parsedTokens
            });
            // Log success or handle the response as needed
            console.log('Successfully fetched and inserted tweets:', response.data);
        } catch (error) {
            console.error('Error fetching tweets from API:', error);
            return res.status(500).json({ message: 'Failed to fetch tweets from API', error: error.message });
        }
        */
    }

    // Send parsed tokens to the token-finding-service
    try {
        const response = await axios.post('http://micro-manager-service:3010/handle-request', {
            tokens: parsedTokens
        });
        const contentType = response.headers['content-type'];

        // If the response is HTML, send it as HTML; otherwise, send it as JSON
        if (contentType.includes('text/html')) {
            res.setHeader('Content-Type', 'text/html');
            res.send(response.data); // Send HTML response directly
        } else {
            // For JSON or other types of content
            res.json(JSON.parse(response.data)); // Parse and send JSON response
        }
    } catch (error) {
        console.error('Error sending tokens to token-finding-service:', error);
        res.status(500).json({ message: 'Failed to fetch tweets', error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Input parsing service listening at http://localhost:${port}`);
});

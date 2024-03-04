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
    
    if (source === 'API') {
        // Placeholder for sending request to the Twitter-fetch microservice
        console.log('Fetching from Twitter API');
        // Example: const twitterData = await axios.post('http://twitter-fetch-service/path', { tokens: parsedTokens });
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

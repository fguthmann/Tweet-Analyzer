const express = require('express');
const app = express();
const port = process.env.PORT || 3001;
const path = require('path');

// Serve static files from the "public" directory
app.use(express.static('public'));

// Send index.html when a GET request is made to the root URL
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Start the server
app.listen(port, () => {
  console.log(`Web interface service listening at http://localhost:${port}`);
});

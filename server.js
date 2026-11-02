const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());

// This variable will hold the LATEST premium tokenized link found by your PC
let latestPremiumM3u8 = "https://placeholder-until-sniffed.com";

// 1. Endpoint where your PC's scraper/sniffer updates the token string
app.get('/update-token', (req, res) => {
    if (req.query.url) {
        latestPremiumM3u8 = req.query.url;
        console.log("🔄 Cloud Server Updated Token:", latestPremiumM3u8);
        return res.send("Token updated successfully on the cloud server");
    }
    res.status(400).send("Missing url parameter");
});

// 2. Fixed endpoint that your Android App Media3 player will connect to
app.get('/play/supersport', (req, res) => {
    console.log("🚀 Global User requested stream. Redirecting to active token...");
    // Redirects your user's Media3 player instantly to the active stream token signature
    res.redirect(latestPremiumM3u8);
});

// Start server engine on Render's dynamic port environment, falling back to 3000
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🟢 Global Relay Server running on port ${PORT}`);
});

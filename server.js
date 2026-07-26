const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir);
}

// Routes mapping
const authRoutes = require('./routes/auth');
const itemRoutes = require('./routes/items');
const adminRoutes = require('./routes/admin');

app.use('/api/auth', authRoutes.router);
app.use('/api/items', itemRoutes);
app.use('/api/admin', adminRoutes);

// Serve HTML pages (fallback)
app.get('/:page', (req, res) => {
    const page = req.params.page;
    const pagePath = path.join(__dirname, 'public', `${page}.html`);
    if (fs.existsSync(pagePath)) {
        res.sendFile(pagePath);
    } else {
        res.sendFile(path.join(__dirname, 'public', 'index.html'));
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

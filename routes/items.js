const express = require('express');
const multer = require('multer');
const path = require('path');
const { getItems, saveItems } = require('../utils/db');
const { verifyToken } = require('./auth');

const router = express.Router();

// Multer storage config
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, path.join(__dirname, '../uploads/'));
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage: storage });

// Get all items
router.get('/', (req, res) => {
    const items = getItems();
    res.json(items);
});

// Get single item
router.get('/:id', (req, res) => {
    const items = getItems();
    const item = items.find(i => i.id === req.params.id);
    if (!item) return res.status(404).json({ message: 'Item not found' });
    res.json(item);
});

// Create item
router.post('/', verifyToken, upload.single('image'), (req, res) => {
    const { title, description, category, type, location, date, contactInfo } = req.body;
    
    const items = getItems();
    const newItem = {
        id: Date.now().toString(),
        userId: req.userId,
        title,
        description,
        category,
        type, // 'lost' or 'found'
        location,
        date,
        contactInfo,
        image: req.file ? `/uploads/${req.file.filename}` : null,
        status: 'open', // open, resolved
        createdAt: new Date().toISOString()
    };

    items.push(newItem);
    saveItems(items);
    res.status(201).json(newItem);
});

// Update item status
router.patch('/:id/status', verifyToken, (req, res) => {
    const { status } = req.body;
    const items = getItems();
    const itemIndex = items.findIndex(i => i.id === req.params.id);
    
    if (itemIndex === -1) return res.status(404).json({ message: 'Item not found' });
    
    // Check ownership or admin
    if (items[itemIndex].userId !== req.userId && req.userRole !== 'admin') {
        return res.status(403).json({ message: 'Not authorized' });
    }

    items[itemIndex].status = status;
    saveItems(items);
    res.json(items[itemIndex]);
});

// Delete item
router.delete('/:id', verifyToken, (req, res) => {
    let items = getItems();
    const item = items.find(i => i.id === req.params.id);
    
    if (!item) return res.status(404).json({ message: 'Item not found' });
    
    // Check ownership or admin
    if (item.userId !== req.userId && req.userRole !== 'admin') {
        return res.status(403).json({ message: 'Not authorized' });
    }

    items = items.filter(i => i.id !== req.params.id);
    saveItems(items);
    res.json({ message: 'Item deleted' });
});

module.exports = router;

const express = require('express');
const { getUsers, saveUsers, getItems, saveItems } = require('../utils/db');
const { verifyToken } = require('./auth');

const router = express.Router();

// Middleware to check admin role
const verifyAdmin = (req, res, next) => {
    if (req.userRole !== 'admin') {
        return res.status(403).json({ message: 'Admin access required' });
    }
    next();
};

// Get stats
router.get('/stats', verifyToken, verifyAdmin, (req, res) => {
    const users = getUsers();
    const items = getItems();
    res.json({
        totalUsers: users.length,
        totalItems: items.length,
        totalLost: items.filter(i => i.type === 'lost').length,
        totalFound: items.filter(i => i.type === 'found').length
    });
});

// Get all users
router.get('/users', verifyToken, verifyAdmin, (req, res) => {
    const users = getUsers().map(({ password, ...user }) => user); // exclude passwords
    res.json(users);
});

// Delete user
router.delete('/users/:id', verifyToken, verifyAdmin, (req, res) => {
    let users = getUsers();
    users = users.filter(u => u.id !== req.params.id);
    saveUsers(users);

    // Also delete user's items
    let items = getItems();
    items = items.filter(i => i.userId !== req.params.id);
    saveItems(items);

    res.json({ message: 'User deleted' });
});

module.exports = router;

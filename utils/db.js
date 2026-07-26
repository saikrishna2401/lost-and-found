const fs = require('fs');
const path = require('path');

const usersFile = path.join(__dirname, '../data/users.json');
const itemsFile = path.join(__dirname, '../data/items.json');

const readData = (file) => {
    try {
        if (!fs.existsSync(file)) {
            fs.writeFileSync(file, JSON.stringify([]));
        }
        const data = fs.readFileSync(file, 'utf-8');
        return JSON.parse(data);
    } catch (err) {
        console.error('Error reading data:', err);
        return [];
    }
};

const writeData = (file, data) => {
    try {
        fs.writeFileSync(file, JSON.stringify(data, null, 2));
    } catch (err) {
        console.error('Error writing data:', err);
    }
};

module.exports = {
    getUsers: () => readData(usersFile),
    saveUsers: (data) => writeData(usersFile, data),
    getItems: () => readData(itemsFile),
    saveItems: (data) => writeData(itemsFile, data),
};

const express = require('express');
const router = express.Router();
const healthCheck = require('../controllers/health');

router.get('/', function(req, res, next) {
    res.setHeader('content-type', 'application/json').send(healthCheck());
});

module.exports = router;
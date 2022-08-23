const express = require('express');
const router = express.Router();
const healthCheck = require('../controllers/health');

router.get('/', function(req, res, next) {
    res.send(healthCheck());
});

module.exports = router;
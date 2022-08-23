const express = require('express');
const router = express.Router();
const healthCheck = require('../controllers/health');

router.get('/', healthCheck);

module.exports = router;
const express = require('express');
const router = express.Router();
const dateUtils = require('../utils/date');

router.get('/health', function(req, res, next) {
    res.send({
        title: 'QuestMaster API',
        version: 1,
        status: 'OK',
        uptime: dateUtils(Math.round(process.uptime())),
        date: new Date()
    });
});

module.exports = router;
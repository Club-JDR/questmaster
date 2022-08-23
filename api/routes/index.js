const express = require('express');
const router = express.Router();

router.get('/health', function(req, res, next) {
    res.send({
        title: 'QuestMaster API',
        version: 1,
        status: 'OK',
        uptime: Math.round(process.uptime()),
        date: new Date()
    });
});

module.exports = router;
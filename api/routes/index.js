const express = require('express');
const router = express.Router();

router.get('/', function(req, res, next) {
    res.send({ title: 'Express App running', version: 1 });
});

module.exports = router;
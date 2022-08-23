const dateUtils = require('../utils/date');

module.exports = (req, res) => {
    res.setHeader('content-type', 'application/json').send({
        title: 'QuestMaster API',
        version: 1,
        status: 'OK',
        uptime: dateUtils(Math.round(process.uptime())),
        date: new Date()
    });
};
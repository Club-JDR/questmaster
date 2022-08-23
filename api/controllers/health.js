const dateUtils = require('../utils/date');

const healthCheck = {
    title: 'QuestMaster API',
    version: 1,
    status: 'OK',
    uptime: dateUtils(Math.round(process.uptime())),
    date: new Date()
}

module.exports = healthCheck;
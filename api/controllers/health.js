const dateUtils = require('../utils/date');

function healthCheck() {
    return {
        title: 'QuestMaster API',
        version: 1,
        status: 'OK',
        uptime: dateUtils(Math.round(process.uptime())),
        date: new Date()
    }
}

module.exports = healthCheck;
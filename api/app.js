const path = require('path');
const express = require('express');
const cookieParser = require('cookie-parser');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');
const cors = require('cors');
const healthRoute = require('./routes/health');

require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const { QUESTMASTER_HOST, QUESTMASTER_PORT, QUESTMASTER_DB_USER, QUESTMASTER_DB_PASSWORD, QUESTMASTER_DB_HOST } = process.env;

// Mongo
mongoose.Promise = global.Promise;
mongoose.connect(`mongodb://${QUESTMASTER_DB_USER}:${QUESTMASTER_DB_PASSWORD}@${QUESTMASTER_DB_HOST}/`, { useNewUrlParser: true, useUnifiedTopology: true });
const db = mongoose.connection;
db.on('error', console.error.bind(console, 'MongoDB connection error:'));

// App config
const app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(cors());
app.disable("x-powered-by");

// Routes
app.use('/health', healthRoute);

// Errors
app.use(function(req, res, next) {
    const err = new Error('Not Found');
    err.status = 404;
    next(err);
});
app.use(function(err, req, res, next) {
    // set locals, only providing error in development
    res.locals.message = err.message;
    res.locals.error = req.app.get('env') === 'development' ? err : {};
    // render the error page
    res.status(err.status || 500);
    res.json({
        message: err.message,
        error: err
    });
});

app.listen(QUESTMASTER_PORT, QUESTMASTER_HOST);
console.log(`Running on http://${QUESTMASTER_HOST}:${QUESTMASTER_PORT}`);
module.exports = app; // for testing
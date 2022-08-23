const mongoose = require("mongoose");
const Schema = mongoose.Schema;
const discordIdRegex = /^.{3,32}#\d{4}$/
const userSchema = new Schema({
    id: {
        type: String,
        required: true,
        match: discordIdRegex,
        unique: true
    },
    isDM: {
        type: Boolean,
        required: true,
    },
    pic: {
        type: String,
        required: true
    },
    _id: false
});
const User = mongoose.model('User', userSchema);
module.exports = User;
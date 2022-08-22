const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
    id: {
        type: String,
        required: true
    },
    isDM: {
        type: Boolean,
        required: true,
        default: false
    },
    pic: {
        type: String,
        required: true
    }
});
const User = model('User', userSchema);
const mongoose = require("mongoose");

const gameSchema = new mongoose.Schema({
    name: {
        type: String,
        required: true
    },
    type: {
        type: String,
        enum: ["oneshot", "campaign"],
        default: "oneshot",
        required: true
    },
    dm: {
        type: {
            mongoose.Schema.Types.ObjectId,
            ref: 'User'
        },
        required: true
    },
    players: {
        type: [{
            mongoose.Schema.Types.ObjectId,
            ref: 'User'
        }]
    },
    system: {
        type: String,
        required: true
    },
    pitch: {
        type: String,
        required: true
    },
    restriction: {
        type: String,
        enum: ["all", "16+", "18+"],
        default: "all"
    },
    restrictionTags: {
        type: [String]
    },
    length: String,
    partySize: {
        type: Number,
        min: 1,
        default: 4,
        max: 99,
        required: true
    },
    selection: {
        type: Boolean,
        default: false
    },
    pregen: {
        type: Boolean,
        default: false
    },
    channel: {
        type: String,
        required: true
    },
    role: {
        type: String,
        required: true
    }
});
const Game = model('Game', gameSchema);
const mongoose = require('mongoose');

const CFG2025Schema = new mongoose.Schema({
    userId: {
        type: String,
        unique: true,
        required: true
    },
    resumeUrl: String,
    resumeKey: String,
    submissionDate: {
        type: Date,
        default: Date.now
    },
    status: {
        type: String,
        enum: ['pending', 'accepted', 'rejected'],
        default: 'pending'
    },
    name: String,
    school: String,
    major: String,
    graduationYear: Number,
    email: {
        type: String,
        unique: true,
        required: true
    }
});

CFG2025Schema.index({ email: 1 }, { unique: true });

module.exports = mongoose.model('CFG2025', CFG2025Schema);
const mongoose = require('mongoose');

const applicationSchema = new mongoose.Schema({
  resumeUrl: String,  // Full S3 URL
  resumeKey: String,  // S3 key for the file
  submissionDate: {
    type: Date,
    default: Date.now
  },
  status: {
    type: String,
    enum: ['pending', 'accepted', 'rejected'],
    default: 'pending'
  }
});

const userSchema = new mongoose.Schema({
  auth0Id: {
    type: String,
    required: true,
    unique: true
  },
  email: {
    type: String,
    required: true
  },
  name: {
    type: String,
    required: true
  },
  school: String,
  major: String,
  graduationYear: Number,
  applications: [applicationSchema],
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('User', userSchema);
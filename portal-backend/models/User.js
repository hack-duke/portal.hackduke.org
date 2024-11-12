const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  gradYear: { type: Number, required: true },
  password: { type: String, required: true },
  resumeUrl: { type: String, required: true },
});

module.exports = mongoose.model('User', UserSchema);

const mongoose = require("mongoose");

const CFG2025Schema = new mongoose.Schema({
  userId: {
    type: String,
    unique: true,
    required: true,
  },
  resumeUrl: String,
  resumeKey: String,
  submissionDate: {
    type: Date,
    default: Date.now,
  },
  status: {
    type: String,
    enum: ["pending", "accepted", "rejected"],
    default: "pending",
  },
  name: String,
  firstName: String,
  lastName: String,
  prefName: String,
  age: Number,
  country: String,
  university: String,
  major: String,
  graduationYear: Number,
  whyhackduke: String,
  whytrack: String,
  email: {
    type: String,
    unique: true,
    required: true,
  },
  phone: {
    type: String,
    required: true,
    unique: true,
  },
  mlh_email_permission: {
    type: Boolean,
    default: false,
  },
});

CFG2025Schema.index({ email: 1 }, { unique: true });

module.exports = mongoose.model("CFG2025", CFG2025Schema);

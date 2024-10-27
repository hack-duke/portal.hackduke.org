const express = require('express');
const router = express.Router();
const multer = require('multer');  
const AWS = require('aws-sdk');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
require('dotenv').config();

const storage = multer.memoryStorage();
const upload = multer({ storage });

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION,
});

router.post('/register', upload.single('resume'), async (req, res) => {
  const { name, email, gradYear, password } = req.body;
  const resumeFile = req.file;

  try {
    // Check if user already exists
    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({ error: 'User already exists' });
    }

    // Hash the password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    // Upload resume to S3
    const s3Params = {
      Bucket: process.env.S3_BUCKET_NAME,
      Key: `${Date.now()}_${resumeFile.originalname}`,
      Body: resumeFile.buffer,
      ContentType: resumeFile.mimetype,
    };

    const s3Response = await s3.upload(s3Params).promise();

    // Create new user
    user = new User({
      name,
      email,
      gradYear,
      password: hashedPassword,
      resumeUrl: s3Response.Location,
    });

    await user.save();
    res.status(201).json({ message: 'User registered successfully' });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;

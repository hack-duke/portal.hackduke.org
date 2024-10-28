const express = require('express');
const router = express.Router();
const multer = require('multer');
const AWS = require('aws-sdk');
const User = require('../models/User'); // Add this import
require('dotenv').config();

// Configure multer for memory storage
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// AWS S3 Configuration
const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION,
});

// Route for submitting an application (only if authenticated)
router.post('/submit', upload.single('resume'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const file = req.file;
  const {
    userId,
    name,
    email,
    school,
    major,
    graduationYear,
    // Add any other fields you want to collect
  } = req.body;

  try {
    // 1. Upload file to S3
    const s3Params = {
      Bucket: process.env.S3_BUCKET_NAME,
      Key: `${userId}/${Date.now()}_${file.originalname}`,
      Body: file.buffer,
      ContentType: 'application/pdf'
    };

    const s3Upload = await s3.upload(s3Params).promise();

    // 2. Create or update user in MongoDB
    const applicationData = {
      auth0Id: userId,
      name,
      email,
      school,
      major,
      graduationYear,
      resumeUrl: s3Upload.Location,
      submissionDate: new Date(),
      status: 'pending'
    };

    // Use findOneAndUpdate to either create or update the user
    const user = await User.findOneAndUpdate(
      { auth0Id: userId },
      { 
        $set: {
          name,
          email,
          school,
          major,
          graduationYear,
        },
        $push: {
          applications: {
            resumeUrl: s3Upload.Location,
            submissionDate: new Date(),
            status: 'pending'
          }
        }
      },
      { 
        new: true, 
        upsert: true // Create if doesn't exist
      }
    );

    res.status(201).json({ 
      message: 'Application submitted successfully', 
      url: s3Upload.Location,
      applicationId: user.applications[user.applications.length - 1]._id
    });

  } catch (error) {
    console.error('Error processing application:', error);
    res.status(500).json({ error: 'Failed to submit application' });
  }
});

// Get application status
router.get('/status/:userId', async (req, res) => {
  try {
    const user = await User.findOne({ auth0Id: req.params.userId });
    if (!user) {
      return res.status(404).json({ error: 'No applications found' });
    }
    res.json(user.applications);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch application status' });
  }
});

module.exports = router;
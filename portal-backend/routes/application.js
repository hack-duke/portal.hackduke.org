const express = require('express');
const router = express.Router();
const multer = require('multer');
const AWS = require('aws-sdk');
require('dotenv').config();

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION,
});

router.post('/submit', upload.single('resume'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const file = req.file;
  const userId = req.body.userId;

  // Create a clean filename
  const fileName = `${Date.now()}_${file.originalname.replace(/[^a-zA-Z0-9.]/g, '_')}`;
  const s3Key = `${userId}/${fileName}`;

  const s3Params = {
    Bucket: process.env.S3_BUCKET_NAME,
    Key: s3Key,
    Body: file.buffer,
    ContentType: 'application/pdf'
  };

  try {
    const data = await s3.upload(s3Params).promise();
    // Store just the S3 key instead of the full URL
    const applicationData = {
      ...req.body,
      resumeKey: s3Key, // Store the S3 key
      resumeUrl: data.Location // Store the full URL as well if needed
    };
    res.status(201).json({ message: 'Application submitted successfully', data: applicationData });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: 'File upload failed' });
  }
});

module.exports = router;
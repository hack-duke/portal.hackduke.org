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

  // Upload resume to S3 under the user's ID
  const s3Params = {
    Bucket: process.env.S3_BUCKET_NAME,
    Key: `${userId}/${Date.now()}_${file.originalname}`,
    Body: file.buffer,
    ContentType: 'application/pdf'
  };

  try {
    const data = await s3.upload(s3Params).promise();
    res.status(201).json({ message: 'Application submitted successfully', url: data.Location });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: 'File upload failed' });
  }
});

router.get('/status', (req, res) => {
  res.send({ status: 'Application status logic here' });
});

module.exports = router;
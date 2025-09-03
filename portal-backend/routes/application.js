const express = require("express");
const router = express.Router();
// const AWS = require("aws-sdk");
const CFG2025Schema = require("../models/Applications/CFG2025");
require("dotenv").config();

// const storage = multer.memoryStorage();
// const upload = multer({ storage: storage });

const CURRENT_SCHEMA = CFG2025Schema; // Change this to the schema you want to use
// WE MUST USE A NEW SCHEMA EVERY SEASON
// const s3 = new AWS.S3({
//   accessKeyId: process.env.AWS_ACCESS_KEY_ID,
//   secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
//   region: process.env.AWS_REGION,
// });

/*
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
    
    const application = new CURRENT_SCHEMA(applicationData);
    await application.save();

    res.status(201).json({ 
      applicationId: application._id
    });
    
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: 'File upload failed' });
  }
});
*/

router.get("/application/:id", async (req, res) => {
  const applicationId = req.params.id;
  const application = await CURRENT_SCHEMA.findById(applicationId).exec();

  if (!application) {
    return res.status(404).json({ error: "Application not found" });
  }

  res.status(200).json(application);
});

router.get("/application", async (req, res) => {
  // This is the endpoint used by normal users
  const userId = req.auth.sub;
  const application = await CURRENT_SCHEMA.findOne({ userId });

  if (application) {
    const {
      status,
      university,
      graduationYear,
      submissionDate,
      name,
      major,
      email,
      firstName,
      lastName,
      prefName,
    } = application;
    res.status(200).json({
      status,
      university,
      graduationYear,
      submissionDate,
      name,
      major,
      email,
      firstName,
      lastName,
      prefName,
    });
  } else {
    res
      .status(404)
      .json({ error: "Application not found with this authentication" });
  }
});

module.exports = router;

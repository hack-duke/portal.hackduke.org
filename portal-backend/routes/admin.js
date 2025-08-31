const express = require("express");
const router = express.Router();
const User = require("../models/User");
const AWS = require("aws-sdk");
require("dotenv").config();

//const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;
const ADMIN_PASSWORD = "password";

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION,
});

// Get all applications (Admin only)
router.post("/applications", async (req, res) => {
  const { password } = req.body;

  if (password !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  try {
    const users = await User.find({}).select(
      "name email school major graduationYear applications",
    );
    res.json(users);
  } catch (error) {
    console.error("Error fetching applications:", error);
    res.status(500).json({ error: "Failed to fetch applications" });
  }
});

// Update application status (Admin only)
router.put("/applications/:applicationId/status", async (req, res) => {
  const { password, status } = req.body;

  if (password !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  try {
    const user = await User.findOne({
      "applications._id": req.params.applicationId,
    });
    if (!user) {
      return res.status(404).json({ error: "Application not found" });
    }

    const application = user.applications.id(req.params.applicationId);
    application.status = status;
    await user.save();

    res.json({ message: "Status updated successfully" });
  } catch (error) {
    console.error("Error updating application status:", error);
    res.status(500).json({ error: "Failed to update status" });
  }
});

router.post("/get-signed-url", async (req, res) => {
  const { password, key } = req.body;

  if (password !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  try {
    // Clean up the key - if it's a full URL, extract just the key part
    let s3Key = key;
    if (key.includes("amazonaws.com")) {
      // Extract everything after the bucket name
      const matches = key.match(/amazonaws\.com\/(.+)$/);
      if (matches && matches[1]) {
        s3Key = decodeURIComponent(matches[1]);
      }
    }

    // Generate signed URL
    const signedUrl = s3.getSignedUrl("getObject", {
      Bucket: process.env.S3_BUCKET_NAME,
      Key: s3Key,
      Expires: 60, // URL expires in 60 seconds
    });

    res.json({ url: signedUrl });
  } catch (error) {
    console.error("Error generating signed URL:", error);
    res.status(500).json({ error: "Failed to generate URL" });
  }
});

module.exports = router;

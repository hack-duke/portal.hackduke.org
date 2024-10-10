const express = require('express');
const mongoose = require('mongoose');
const userRoutes = require('./routes/user');
const applicationRoutes = require('./routes/application');

require('dotenv').config();

const { S3Client, PutObjectCommand, GetObjectCommand , HeadBucketCommand} = require('@aws-sdk/client-s3');

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
});

const app = express();

mongoose.connect(process.env.MONGODB_URI);

app.use(express.json());

app.use('/api/users', userRoutes);
app.use('/api/applications', applicationRoutes);

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));



const testS3Connection = async (bucketName) => {
    const command = new HeadBucketCommand({ Bucket: bucketName });
    try {
      await s3.send(command);
      console.log(`S3 Connection successful. Bucket "${bucketName}" is accessible.`);
    } catch (error) {
      console.error(`S3 Connection failed for bucket "${bucketName}":`, error.message);
    }
  };
  
testS3Connection(process.env.S3_BUCKET_NAME);


// const uploadToS3 = async (bucketName, key, body) => {
//   const command = new PutObjectCommand({
//     Bucket: bucketName,
//     Key: key,
//     Body: body,
//   });
  
//   try {
//     const data = await s3.send(command);
//     console.log('File uploaded successfully', data);
//   } catch (error) {
//     console.error('Error uploading file', error);
//   }
// };



const express = require('express');
const mongoose = require('mongoose');
const { expressjwt: jwt } = require('express-jwt');
const jwksRsa = require('jwks-rsa');
const userRoutes = require('./routes/user');
const applicationRoutes = require('./routes/application');
const adminRoutes = require('./routes/admin');
const debugRoutes = require('./routes/debug');
const ticketsRoutes = require('./routes/tickets');
const cors = require('cors');
require('dotenv').config();

const { S3Client, PutObjectCommand, HeadBucketCommand } = require('@aws-sdk/client-s3');

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
});

const app = express();

app.use(cors({
  origin: process.env.FRONTEND_URL,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

app.use(express.json());

mongoose.connect(process.env.MONGODB_URI)
  .then(() => console.log('MongoDB connected'))
  .catch((err) => console.error('MongoDB connection error:', err));

// JWT Middleware for Auth0
const checkJwt = jwt({
  secret: jwksRsa.expressJwtSecret({
    cache: true,
    rateLimit: true,
    jwksRequestsPerMinute: 5,
    jwksUri: `https://${process.env.AUTH0_DOMAIN}/.well-known/jwks.json`,
  }),
  audience: process.env.AUTH0_AUDIENCE,
  issuer: `https://${process.env.AUTH0_DOMAIN}/`,
  algorithms: ['RS256'],
});

app.use('/api/admin', adminRoutes);
app.use('/tickets', ticketsRoutes);
app.use('/api/users', userRoutes);
app.use('/api/applications', checkJwt, applicationRoutes);
app.use('/api/debug', debugRoutes);
app.get('/health', (req, res) => res.send('Server is running'));

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
  
// testS3Connection(process.env.S3_BUCKET_NAME);


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


testS3Connection(process.env.S3_BUCKET_NAME);

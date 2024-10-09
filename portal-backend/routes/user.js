const express = require('express');
const router = express.Router();
const multer = require('multer');  
const AWS = require('aws-sdk');
const User = require('../models/User');

// S3 setup 
const s3 = new AWS.S3();

const upload = multer({ dest: 'uploads/' });  // handle files

// new user
router.post('/register', upload.single('resume'), (req, res) => {
    // register logic here
  res.status(201).send({ message: 'User registered successfully' });
});

router.get('/:id', (req, res) => {
  //get user detais here
  res.send({ message: 'User details here' });
});

module.exports = router;

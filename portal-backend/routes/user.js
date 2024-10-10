const express = require('express');
const router = express.Router();
const multer = require('multer');  
const User = require('../models/User');



const upload = multer({ dest: 'uploads/' });  

router.post('/register', upload.single('resume'), (req, res) => {
  res.status(201).send({ message: 'User registered successfully' });
});

router.get('/:id', (req, res) => {
  res.send({ message: 'User details here' });
});

module.exports = router;

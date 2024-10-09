const express = require('express');
const router = express.Router();

router.post('/submit', (req, res) => {
  //subnmit app logic here
  res.status(201).send({ message: 'Application submitted' });
});

router.get('/status', (req, res) => {
  // app status here. 
  res.send({ status: 'Application status logic here' });
});

module.exports = router;

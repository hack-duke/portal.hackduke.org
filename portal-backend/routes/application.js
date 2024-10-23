const express = require('express');
const router = express.Router();

const applications = [
  {
    id: 1,
    name: 'Janet Meng',
    email: 'janet.meng@example.com',
    status: 'Submitted',
    submissionDate: '2024-10-22',
    ratings: []
  },
  {
    id: 2,
    name: 'Alex Johnson',
    email: 'alex.johnson@example.com',
    status: 'Under Review',
    submissionDate: '2024-10-20',
    ratings: []
  },
  {
    id: 3,
    name: 'Maria Smith',
    email: 'maria.smith@example.com',
    status: 'Approved',
    submissionDate: '2024-10-18',
    ratings: []
  }
];

router.post('/submit', (req, res) => {
  //subnmit app logic here
  console.log(req.body);
  res.status(201).send({ message: 'Application submitted' });
});

router.post('/rate/:id', (req, res) =>{
  const applicationId = parseInt(req.params.id);
  // const { rating } = req.body;
  const ratings = req.body.ratings; 

  if (!Array.isArray(ratings) || ratings.length === 0) {
    return res.status(400).send({ error: 'Ratings must be an array with at least one rating' });
  }
 
  const application = applications.find(app => app.id === applicationId);

  if (!application) {
    return res.status(404).send({ error: 'Application not found' });
  }
 
  for (let rate of ratings)
    if (rate < 1 || rate > 5) {
      return res.status(400).send({ error: 'Each rating must be a number between 1 and 5' });
    }
  
  application.ratings.push({ ratings, date: new Date() });

  res.status(201).send({ message: `Ratings added to application ${applicationId}` });
});

router.get('/status', (req, res) => {
  // app status here. 
  res.send({ status: 'Application status logic here' });
});

router.get('/fetch/:id', (req, res) => {
  const applicationId = parseInt(req.params.id);
  const application = applications.find(app => app.id === applicationId);

  if (!application){
    return res.status(404).send({ error: 'Application not found' });
  }

  res.send(application);
  console.log(req.body);
  res.send({ status: "Application Fetched" });
});

module.exports = router;

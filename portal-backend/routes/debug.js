const express = require('express');
const router = express.Router();

router.post('/log', async (req, res) => {
    console.error('--------------BEGIN DEBUG--------------')
    console.error(req.headers);
    console.error(req.body);
    console.error('TIME STAMP: ' + Date.now())
    console.error('--------------END DEBUG--------------')
    res.status(200).send({ message: 'Logged' });
})

module.exports = router;
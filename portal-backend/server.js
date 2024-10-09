const express = require('express');
const mongoose = require('mongoose');
const userRoutes = require('./routes/user');
const applicationRoutes = require('./routes/application');

const app = express();

// MongoDB connection 
mongoose.connect('mongodb://localhost:27017/hackduke', { useNewUrlParser: true, useUnifiedTopology: true });

app.use(express.json());

app.use('/api/users', userRoutes);
app.use('/api/applications', applicationRoutes);

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

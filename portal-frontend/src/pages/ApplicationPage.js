import React, { useEffect, useState } from 'react';
import axios from 'axios';

const ApplicationPage = () => {
  const [applicationStatus, setApplicationStatus] = useState(null);

  useEffect(() => {
    // get application status
    axios.get('/api/application-status')
      .then(response => {
        setApplicationStatus(response.data.status);
      });
  }, []);

  const handleSubmitApplication = () => {
    // app submit logic here
  };

  return (
    <div>
      <h2>Application Page</h2>
      <button onClick={handleSubmitApplication}>Submit Application</button>
      <p>Status: {applicationStatus || "No application submitted yet"}</p>
    </div>
  );
};

export default ApplicationPage;

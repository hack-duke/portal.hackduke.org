import React, { useState } from 'react';
import axios from 'axios';

const AdminPage = () => {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [applications, setApplications] = useState([]);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showPDF, setShowPDF] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/admin/applications', {
        password
      });
      setApplications(response.data);
      setIsAuthenticated(true);
      setError(null);
    } catch (error) {
      setError('Invalid password');
    }
  };

  const handleStatusUpdate = async (applicationId, newStatus) => {
    try {
      await axios.put(`http://localhost:5000/api/admin/applications/${applicationId}/status`, {
        password,
        status: newStatus
      });
      
      // Refresh applications after status update
      const response = await axios.post('http://localhost:5000/api/admin/applications', {
        password
      });
      setApplications(response.data);
    } catch (error) {
      setError('Failed to update status');
    }
  };

  const getSignedUrl = async (key) => {
    try {
      const response = await axios.post('http://localhost:5000/api/admin/get-signed-url', {
        password,
        key
      });
      return response.data.url;
    } catch (error) {
      setError('Failed to get resume URL');
      return null;
    }
  };

  const handleViewResume = async (application) => {
    try {
      const key = application.resumeKey || application.resumeUrl;
      const response = await axios.post('http://localhost:5000/api/admin/get-signed-url', {
        password,
        key
      });
      setShowPDF(response.data.url);
    } catch (error) {
      setError('Failed to get resume URL');
    }
  };

  const nextApplication = () => {
    if (currentIndex < applications.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowPDF(false);
    }
  };

  const previousApplication = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setShowPDF(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div>
        <h2>Admin Login</h2>
        <form onSubmit={handleLogin}>
          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit">Login</button>
          {error && <div style={{ color: 'red' }}>{error}</div>}
        </form>
      </div>
    );
  }

  if (applications.length === 0) {
    return <div>No applications found.</div>;
  }

  const currentApp = applications[currentIndex];
  const application = currentApp.applications[currentApp.applications.length - 1];

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <div style={{ display: 'flex' }}>
        <div style={{ flex: '1', marginRight: '20px' }}>
          <h3>Application {currentIndex + 1} of {applications.length}</h3>
          
          <div style={{ margin: '20px 0' }}>
            <button onClick={previousApplication} disabled={currentIndex === 0}>
              Previous
            </button>
            <button onClick={nextApplication} disabled={currentIndex === applications.length - 1}>
              Next
            </button>
          </div>

          <div>
            <h4>Applicant Information:</h4>
            <p><strong>Name:</strong> {currentApp.name}</p>
            <p><strong>Email:</strong> {currentApp.email}</p>
            <p><strong>School:</strong> {currentApp.school}</p>
            <p><strong>Major:</strong> {currentApp.major}</p>
            <p><strong>Graduation Year:</strong> {currentApp.graduationYear}</p>
            <p><strong>Status:</strong> {application.status}</p>
            <button onClick={() => handleViewResume(application)}>
                View Resume
            </button>
          </div>

          <div style={{ margin: '20px 0' }}>
            <h4>Update Status:</h4>
            <button 
              onClick={() => handleStatusUpdate(application._id, 'accepted')}
              style={{ backgroundColor: 'green', color: 'white', marginRight: '10px' }}
            >
              Accept
            </button>
            <button 
              onClick={() => handleStatusUpdate(application._id, 'rejected')}
              style={{ backgroundColor: 'red', color: 'white', marginRight: '10px' }}
            >
              Reject
            </button>
            <button 
              onClick={() => handleStatusUpdate(application._id, 'pending')}
            >
              Mark as Pending
            </button>
          </div>
        </div>

        {showPDF && (
          <div style={{ flex: '1' }}>
            <iframe
              src={showPDF}
              title="Resume PDF"
              width="100%"
              height="800px"
              style={{ border: 'none' }}
            />
          </div>
        )}
      </div>

      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  );
};

export default AdminPage;
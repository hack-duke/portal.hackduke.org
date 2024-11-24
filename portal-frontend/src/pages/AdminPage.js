import React, { useState } from 'react';
import axios from 'axios';
import { Navbar } from '../components/navbar';

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
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/admin/applications`, {
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
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/admin/applications/${applicationId}/status`, {
        password,
        status: newStatus
      });
      
      // Refresh applications after status update
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/admin/applications`, {
        password
      });
      setApplications(response.data);
    } catch (error) {
      setError('Failed to update status');
    }
  };

  const getSignedUrl = async (key) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/admin/get-signed-url`, {
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
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/admin/get-signed-url`, {
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
      <div class="hero-bg-1">
        <img class="bg-picture-left" id="hero-bg-smallRedSquare" src="/images/bg-smallRedSquare.svg" alt="Small Red Square"></img>
        <img class="bg-picture-left" id="hero-bg-blueSgwiggly" src="/images/bg-blueSgwiggly.svg" alt="Blue Sgwiggly" />   
        <img class="bg-picture-left" id="hero-bg-greenQuarterCircle" src="/images/bg-greenQuarterCircle.svg" alt="Green Quarter Circle"></img>
        <img class="bg-picture-left" id="hero-bg-bigYellowTraingle" src="/images/bg-bigYellowTriangle.svg" alt="Big Yellow Triangle"></img>
        <img class="bg-picture-left" id="hero-bg-whiteSnowflake" src="/images/bg-whiteSnowflake.svg" alt="White Snowflake"></img>
        <img class="bg-picture-left" id="hero-bg-blueSnowflake" src="/images/bg-blueSnowflake.svg" alt="Blue Snowflake"></img>
      </div>

      {/* Elements on the left that do NOT move */}
      <div class="hero-bg-2">
        <img class="bg-picture-right" id="hero-bg-blueBlob" src="/images/bg-blueBlob.svg" alt="Blue Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowRing" src="/images/bg-yellowRing.svg" alt="Yellow Ring"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlob" src="/images/bg-orangeBlob.svg" alt="Orange Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-blueTriangle" src="/images/bg-blueTriangle.svg" alt="Blue Triangle"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlobLining" src="/images/bg-orangeBlobLining.svg" alt="Orange Blob Lining"></img>
        <img class="bg-picture-right" id="hero-bg-whiteSquare" src="/images/bg-whiteSquare.svg" alt="White Square"></img>
        <img class="bg-picture-right" id="hero-bg-redSnowflake" src="/images/bg-redSnowflake.svg" alt="Red Snowflake"></img>
      </div>

      {/* Elements on the left that do move */}
      <div class="hero-bg-3">
        <img class="bg-picture-right" id="hero-bg-greenOval" src="/images/bg-greenOval.svg" alt="Green Oval Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowCircle" src="/images/bg-yellowCircle.svg" alt="Yellow Circle"></img>
        <img class="bg-picture-right" id="hero-bg-redSwiggly" src="/images/bg-redSgwiggly.svg" alt="Red Swiggly Line"></img>
        <img class="bg-picture-right" id="hero-bg-greenSnowflake" src="/images/bg-greenSnowflake.svg" alt="Green Snowflake"></img>
      </div>

      {/*Elements on the right that do move*/}
      <div class="hero-bg-4">
        <img class="bg-picture-left" id="hero-bg-blueDashedCircle" src="/images/bg-blueDashedCircle.svg" alt="Blue Dashed Circle" />
        <img class="bg-picture-left" id="hero-bg-greenCircle" src="/images/bg-greenCircle.svg" alt="Green Circle" />
        <img class="bg-picture-left" id="hero-bg-yellowSquare" src="/images/bg-yellowSquare.svg" alt="Yellow Square" />
        <img class="bg-picture-left" id="hero-bg-yellowTriangle" src="/images/bg-yellowTriangle.svg" alt="Yellow Triangle" />       
        <img class="bg-picture-left" id="hero-bg-redSquare" src="/images/bg-redSquare.svg" alt="Red Square" />
        <img class="bg-picture-left" id="hero-bg-redLine" src="/images/bg-redLine.svg" alt="Red Line" />
        <img class="bg-picture-left" id="hero-bg-greenSquare" src="/images/bg-greenSquare.svg" alt="Green Square" />
        {/* <img class="bg-picture-left" id="hero-bg-yellowSnowflake" src="/images/bg-yellowSnowflake.svg" alt="Yellow Snowflake" /> */}
        <img class="bg-picture-left" id="hero-bg-redDashedCircle" src="/images/bg-redDashedCircle.svg" alt="Red Dashed Circle" />
      </div>
        <Navbar/>
        <h1 className="login-heading">
          Admin Log In
        </h1>
        <form onSubmit={handleLogin}>
          <div className = "passwordForm">
            <label class = "passwordLabel">Password:</label>
            <input
              class = "passwordInput"
              type = "password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button 
          className="admin-login-button"
          style={{
            backgroundImage: `url('/images/Log_In_Button.png')`,
          }}
          type="submit">Login</button>
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
      <div class="hero-bg-1">
        <img class="bg-picture-left" id="hero-bg-smallRedSquare" src="/images/bg-smallRedSquare.svg" alt="Small Red Square"></img>
        <img class="bg-picture-left" id="hero-bg-blueSgwiggly" src="/images/bg-blueSgwiggly.svg" alt="Blue Sgwiggly" />   
        <img class="bg-picture-left" id="hero-bg-greenQuarterCircle" src="/images/bg-greenQuarterCircle.svg" alt="Green Quarter Circle"></img>
        <img class="bg-picture-left" id="hero-bg-bigYellowTraingle" src="/images/bg-bigYellowTriangle.svg" alt="Big Yellow Triangle"></img>
        <img class="bg-picture-left" id="hero-bg-whiteSnowflake" src="/images/bg-whiteSnowflake.svg" alt="White Snowflake"></img>
        <img class="bg-picture-left" id="hero-bg-blueSnowflake" src="/images/bg-blueSnowflake.svg" alt="Blue Snowflake"></img>
      </div>

      {/* Elements on the left that do NOT move */}
      <div class="hero-bg-2">
        <img class="bg-picture-right" id="hero-bg-blueBlob" src="/images/bg-blueBlob.svg" alt="Blue Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowRing" src="/images/bg-yellowRing.svg" alt="Yellow Ring"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlob" src="/images/bg-orangeBlob.svg" alt="Orange Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-blueTriangle" src="/images/bg-blueTriangle.svg" alt="Blue Triangle"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlobLining" src="/images/bg-orangeBlobLining.svg" alt="Orange Blob Lining"></img>
        <img class="bg-picture-right" id="hero-bg-whiteSquare" src="/images/bg-whiteSquare.svg" alt="White Square"></img>
        <img class="bg-picture-right" id="hero-bg-redSnowflake" src="/images/bg-redSnowflake.svg" alt="Red Snowflake"></img>
      </div>

      {/* Elements on the left that do move */}
      <div class="hero-bg-3">
        <img class="bg-picture-right" id="hero-bg-greenOval" src="/images/bg-greenOval.svg" alt="Green Oval Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowCircle" src="/images/bg-yellowCircle.svg" alt="Yellow Circle"></img>
        <img class="bg-picture-right" id="hero-bg-redSwiggly" src="/images/bg-redSgwiggly.svg" alt="Red Swiggly Line"></img>
        <img class="bg-picture-right" id="hero-bg-greenSnowflake" src="/images/bg-greenSnowflake.svg" alt="Green Snowflake"></img>
      </div>

      {/*Elements on the right that do move*/}
      <div class="hero-bg-4">
        <img class="bg-picture-left" id="hero-bg-blueDashedCircle" src="/images/bg-blueDashedCircle.svg" alt="Blue Dashed Circle" />
        <img class="bg-picture-left" id="hero-bg-greenCircle" src="/images/bg-greenCircle.svg" alt="Green Circle" />
        <img class="bg-picture-left" id="hero-bg-yellowSquare" src="/images/bg-yellowSquare.svg" alt="Yellow Square" />
        <img class="bg-picture-left" id="hero-bg-yellowTriangle" src="/images/bg-yellowTriangle.svg" alt="Yellow Triangle" />       
        <img class="bg-picture-left" id="hero-bg-redSquare" src="/images/bg-redSquare.svg" alt="Red Square" />
        <img class="bg-picture-left" id="hero-bg-redLine" src="/images/bg-redLine.svg" alt="Red Line" />
        <img class="bg-picture-left" id="hero-bg-greenSquare" src="/images/bg-greenSquare.svg" alt="Green Square" />
        {/* <img class="bg-picture-left" id="hero-bg-yellowSnowflake" src="/images/bg-yellowSnowflake.svg" alt="Yellow Snowflake" /> */}
        <img class="bg-picture-left" id="hero-bg-redDashedCircle" src="/images/bg-redDashedCircle.svg" alt="Red Dashed Circle" />
      </div>

      <Navbar />
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
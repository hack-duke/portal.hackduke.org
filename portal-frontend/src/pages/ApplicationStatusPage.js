import React, { useEffect, useState } from 'react';
import HeroBackground from '../components/HeroBackground';
import { Navbar } from '../components/Navbar';
import './ApplicationStatusPage.css';
import { useAuth0 } from '@auth0/auth0-react';
import { formatDistanceToNow } from 'date-fns';
import { FullPageLoadingSpinner } from '../components/FullPageLoadingSpinner';
import { useWindowSize } from 'react-use';
import Confetti from 'react-confetti';
import { useLocation } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import Button from '../components/Button';

const StatusList = ({ statusItems }) => {
  return (
    <div className="status-grid">
      {statusItems.map((item, index) => (
        <div key={index}>
          <div className='status-label'>{item.label}</div>
          <div className='status-value'>{item.value}</div>
        </div>
      ))}
    </div>
  );
};

const formatApplication = (application) => {
  var ret = [];
  ret.push({ 'label': 'name', 'value': (application['prefName'] || application['firstName']) + ' ' + application['lastName'] })
  ret.push({ 'label': 'email', 'value': application['email'] })
  ret.push({ 'label': 'status', 'value': application['status'] })
  ret.push({ 'label': 'grad year', 'value': application['graduationYear'] })
  ret.push({ 'label': 'university', 'value': application['university'] })
  ret.push({ 'label': 'major', 'value': application['major'] })
  ret.push({ 'label': 'submitted', 'value': formatDistanceToNow(new Date(application['submissionDate']), { addSuffix: true }) })

  return ret;
}

const ApplicationStatusPage = () => {
  const { user, getAccessTokenSilently } = useAuth0();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const { width, height } = useWindowSize();
  const location = useLocation();
  const { firstTime } = location.state || {};

  useEffect(() => {
    const checkIfSubmitted = async () => {
      setLoading(true);
      const token = await getAccessTokenSilently();
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/applications/application`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.status !== 200) {
        const js = await response.json();
        setError(js.error);
      }
      else {
        const json = await response.json();
        setApplication(formatApplication(json));
      }
      setLoading(false);
    }

    checkIfSubmitted();
  }, [getAccessTokenSilently]);

  console.log();

  return (
    <>
      <Navbar />
      <HeroBackground />
      {loading && <FullPageLoadingSpinner />}
      {
        firstTime &&
        <div className='confetti'>
          <Confetti
            width={width}
            height={height}
            recycle={false}
            numberOfPieces={400}
          />
        </div>
      }
      <h1 className='status-title'>Applicant Status</h1>
      {error && <p>{error}</p>}

      {application && <div className='status-container'>
        <StatusList statusItems={application} />

      </div>}


      {application && application[2]['value'].includes('confirmed') && (
        <>
					<Button variant="secondary" className="checkin-button" onClick={() => setShowQRModal(true)}>Check-In Code</Button>
          {showQRModal && (
            <div 
              className="qr-modal-overlay"
              onClick={() => setShowQRModal(false)}
            >
              <div className="qr-modal-content">
                <QRCodeSVG 
                  value={user.sub} 
                  size={Math.min(width * 0.8, height * 0.8)} 
                  marginSize={2} 
                  minVersion={6}
                />
              </div>
            </div>
          )}
        </>
      )}

    </>
  );
};

export default ApplicationStatusPage;

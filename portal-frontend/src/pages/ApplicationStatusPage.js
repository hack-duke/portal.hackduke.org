import React, { useEffect, useState } from 'react';
import HeroBackground from '../components/HeroBackground';
import { Navbar } from '../components/Navbar';
import './ApplicationStatusPage.css'
import { useAuth0 } from '@auth0/auth0-react';
import { formatDistanceToNow } from 'date-fns';
import { FullPageLoadingSpinner } from '../components/FullPageLoadingSpinner';
import { useWindowSize } from 'react-use';
import Confetti from 'react-confetti'
import { useLocation } from 'react-router-dom';

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
  ret.push({ 'label': 'name', 'value': application['name'] })
  ret.push({ 'label': 'email', 'value': application['email'] })
  ret.push({ 'label': 'status', 'value': application['status'] })
  ret.push({ 'label': 'grad year', 'value': application['graduationYear'] })
  ret.push({ 'label': 'university', 'value': application['university'] })
  ret.push({ 'label': 'major', 'value': application['major'] })
  ret.push({ 'label': 'submitted', 'value': formatDistanceToNow(new Date(application['submissionDate']), { addSuffix: true }) })

  return ret
}

const ApplicationStatusPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [application, setApplication] = useState(null)
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { width, height } = useWindowSize();
  const location = useLocation();
  const { firstTime } = location.state || {};

  useEffect(
    () => {
      const checkIfSubmitted = async () => {
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
          setApplication(formatApplication(json))
        }
      }

      setLoading(true);
      checkIfSubmitted()
      setLoading(false);
    },
    []
  )

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
      {error & <p>{error}</p>}

      {application && <div className='status-container'>

        <StatusList statusItems={application} />
      </div>}
    </>
  );
};

export default ApplicationStatusPage;

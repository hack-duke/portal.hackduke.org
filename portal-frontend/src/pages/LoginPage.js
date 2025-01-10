import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { HeroBackground } from '../components/HeroBackground';
import { useEffect } from 'react';
import Button from '../components/Button';
import './LoginPage.css'
import Countdown from 'react-countdown';
import CountdownRenderer from '../components/CountdownRenderer';

const LoginPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  useEffect(() => {
    document.body.style.overflow = 'hidden';
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    <>
      <div className="hero">
        <HeroBackground />
        
        <h1 className="hero-text">Apply Now</h1>
        <div className='buttons-container'>
          <Button className="hero-button" onClick={() => loginWithRedirect({ screen_hint: 'signup' })}>
            Participant
          </Button>
          <Button className="mentor-button" variant='secondary' onClick={() => window.open("https://forms.gle/gtWwViqvjWqsXBo5A", "_blank")}>
            Mentor/Judge
          </Button>
        </div>

        <Countdown date={new Date("2025-01-31")} renderer={CountdownRenderer}/>
      </div>
    </>
  );
};

export default LoginPage;

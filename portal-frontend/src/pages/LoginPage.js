import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { HeroBackground } from '../components/HeroBackground';
import { useEffect } from 'react';
import Button from '../components/Button';
import './LoginPage.css'

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
        <Button className="hero-button" onClick={() => loginWithRedirect({ screen_hint: 'signup' })}>
          Log In
        </Button>
      </div>
    </>
  );
};

export default LoginPage;

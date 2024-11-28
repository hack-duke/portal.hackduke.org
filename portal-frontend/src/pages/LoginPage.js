import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { HeroBackground } from '../components/HeroBackground';
import { useEffect } from 'react';
import '../App.css';
import Button from '../components/Button';

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
    <div className="index">
        <div className="hero">
            <HeroBackground />
            {/* make a large white text in urbanist font that says "Apply Now!" */}
            <div className="hero-text">
                <h1>Apply Now</h1>
            </div>
            <button className="hero-button">Log In</button>

        </div>
    </div>

</>
  );
};

export default LoginPage;

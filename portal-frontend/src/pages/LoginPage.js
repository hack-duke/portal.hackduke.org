import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Background } from '../components/Background';
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
    <div>

      <Background />

      <Navbar />

      <h1 className="login-heading">
        Log In
      </h1>
      <Button className="login-button" onClick={() => loginWithRedirect()}> 
        register
      </Button>
    </div>
  );
};

export default LoginPage;

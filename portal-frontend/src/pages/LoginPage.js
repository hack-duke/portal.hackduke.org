import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { Navbar } from '../components/navbar';

const LoginPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    <div style = {{
      backgroundImage: `url(/images/Login.png)`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      height: '100vh',
      width: '100vw',
    }}>
      <Navbar />
      <h2>Login</h2>
      <button onClick={() => loginWithRedirect()}>Log In</button>
    </div>
  );
};

export default LoginPage;
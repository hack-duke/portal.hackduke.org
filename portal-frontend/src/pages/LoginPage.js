import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';

const LoginPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    <div>
      <h2>Login</h2>
      <button onClick={() => loginWithRedirect()}>Log In</button>
    </div>
  );
};

export default LoginPage;
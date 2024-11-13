import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';

const RegisterPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    <div>
      <h2>Register</h2>
      <button onClick={() => loginWithRedirect({ screen_hint: 'signup' })}>
        Register
      </button>
    </div>
  );
};

export default RegisterPage;
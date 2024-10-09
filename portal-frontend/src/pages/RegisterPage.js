import React from 'react';

const RegisterPage = () => {
  const handleRegister = () => {
    // implement register here -- need to add Auth0 and shubboleth stuff
  };

  return (
    <div>
      <h2>Register Page</h2>
      <button onClick={handleRegister}>Register</button>
    </div>
  );
};

export default RegisterPage;

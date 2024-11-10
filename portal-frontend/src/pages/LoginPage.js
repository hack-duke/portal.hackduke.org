import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { Navbar } from '../components/navbar';
import { useEffect } from 'react';

const LoginPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  useEffect(() => {
    document.body.style.overflow = 'hidden';
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    
    <div style = {{
      position: 'relative',
      backgroundImage: `url(/images/BG_Elements.svg)`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      height: '100vh',
      width: '100vw',
      left: '-10px',
    }}>
      <Navbar />

      <div> 
        
      </div>
      <h2 style = {{
        position: 'relative',
        background: '#0042C6',
        font: 'urbanist',
        width: '10.2vw',                     // Set responsive width based on viewport width
        height: '3.75vw',                  // Set responsive height based on viewport width to maintain aspect ratio
        // marginTop: '59.5vh',                 // Adjust based on the layout
        // marginLeft: '62vw',
      }}>Login</h2>

      <button
        style={{
          backgroundImage: `url('/images/Log_In_Button.png')`,
          backgroundSize: 'cover',           // Ensures the image covers the button's area
          backgroundPosition: 'center',      // Centers the image within the button
          backgroundRepeat: 'no-repeat',     // Prevents the image from tiling
          width: '10.2vw',                     // Set responsive width based on viewport width
          height: '3.75vw',                  // Set responsive height based on viewport width to maintain aspect ratio
          marginTop: '59.5vh',                 // Adjust based on the layout
          marginLeft: '62vw',
          border: 'none',
          cursor: 'pointer',
          color: 'transparent',
          backgroundColor: 'transparent',    // Ensures no extra background color
          position: 'absolute',              // Allows precise placement with margin values
        }}
        onClick={() => loginWithRedirect()}
      >
        Log In
      </button>


    </div>
  );
};

export default LoginPage;
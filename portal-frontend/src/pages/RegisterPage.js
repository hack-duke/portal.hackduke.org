import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { Navbar } from '../components/navbar';
import { useEffect } from 'react';

const RegisterPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();

  useEffect(() => {
    document.body.style.overflow = 'hidden';
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/application" replace />;
  }

  return (
    <div style={{
      position: 'relative',
      // backgroundImage: `url(/images/BG_Elements.svg)`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      height: '100vh',
      width: '100vw',
      left: '-10px',
    }}>
      <div class = "hero-background" style={{
        position: 'relative',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        height: '100vh',
        width: '100vw',
        // bottom: '100px',
      }}>
      {/* Elements on the right that do NOT move */}
      <div class="hero-bg-1">
        <img class="bg-picture-left" id="hero-bg-smallRedSquare" src="/images/bg-smallRedSquare.svg" alt="Small Red Square"></img>
        <img class="bg-picture-left" id="hero-bg-blueSgwiggly" src="/images/bg-blueSgwiggly.svg" alt="Blue Sgwiggly" />   
        <img class="bg-picture-left" id="hero-bg-greenQuarterCircle" src="/images/bg-greenQuarterCircle.svg" alt="Green Quarter Circle"></img>
        <img class="bg-picture-left" id="hero-bg-bigYellowTraingle" src="/images/bg-bigYellowTriangle.svg" alt="Big Yellow Triangle"></img>
        <img class="bg-picture-left" id="hero-bg-whiteSnowflake" src="/images/bg-whiteSnowflake.svg" alt="White Snowflake"></img>
        <img class="bg-picture-left" id="hero-bg-blueSnowflake" src="/images/bg-blueSnowflake.svg" alt="Blue Snowflake"></img>
      </div>

      {/* Elements on the left that do NOT move */}
      <div class="hero-bg-2">
        <img class="bg-picture-right" id="hero-bg-blueBlob" src="/images/bg-blueBlob.svg" alt="Blue Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowRing" src="/images/bg-yellowRing.svg" alt="Yellow Ring"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlob" src="/images/bg-orangeBlob.svg" alt="Orange Blob Shape"></img>
        <img class="bg-picture-right" id="hero-bg-blueTriangle" src="/images/bg-blueTriangle.svg" alt="Blue Triangle"></img>
        <img class="bg-picture-right" id="hero-bg-orangeBlobLining" src="/images/bg-orangeBlobLining.svg" alt="Orange Blob Lining"></img>
        <img class="bg-picture-right" id="hero-bg-whiteSquare" src="/images/bg-whiteSquare.svg" alt="White Square"></img>
        <img class="bg-picture-right" id="hero-bg-redSnowflake" src="/images/bg-redSnowflake.svg" alt="Red Snowflake"></img>
      </div>

      {/* Elements on the left that do move */}
      <div class="hero-bg-3">
        <img class="bg-picture-right" id="hero-bg-greenOval" src="/images/bg-greenOval.svg" alt="Green Oval Shape"></img>
        <img class="bg-picture-right" id="hero-bg-yellowCircle" src="/images/bg-yellowCircle.svg" alt="Yellow Circle"></img>
        <img class="bg-picture-right" id="hero-bg-redSwiggly" src="/images/bg-redSgwiggly.svg" alt="Red Swiggly Line"></img>
        <img class="bg-picture-right" id="hero-bg-greenSnowflake" src="/images/bg-greenSnowflake.svg" alt="Green Snowflake"></img>
      </div>

      {/*Elements on the right that do move*/}
      <div class="hero-bg-4">
        <img class="bg-picture-left" id="hero-bg-blueDashedCircle" src="/images/bg-blueDashedCircle.svg" alt="Blue Dashed Circle" />
        <img class="bg-picture-left" id="hero-bg-greenCircle" src="/images/bg-greenCircle.svg" alt="Green Circle" />
        <img class="bg-picture-left" id="hero-bg-yellowSquare" src="/images/bg-yellowSquare.svg" alt="Yellow Square" />
        <img class="bg-picture-left" id="hero-bg-yellowTriangle" src="/images/bg-yellowTriangle.svg" alt="Yellow Triangle" />       
        <img class="bg-picture-left" id="hero-bg-redSquare" src="/images/bg-redSquare.svg" alt="Red Square" />
        <img class="bg-picture-left" id="hero-bg-redLine" src="/images/bg-redLine.svg" alt="Red Line" />
        <img class="bg-picture-left" id="hero-bg-greenSquare" src="/images/bg-greenSquare.svg" alt="Green Square" />
        {/* <img class="bg-picture-left" id="hero-bg-yellowSnowflake" src="/images/bg-yellowSnowflake.svg" alt="Yellow Snowflake" /> */}
        <img class="bg-picture-left" id="hero-bg-redDashedCircle" src="/images/bg-redDashedCircle.svg" alt="Red Dashed Circle" />
      </div>
    </div>
    <Navbar />

    <h1 className="login-heading">
        Register
      </h1>
      <button className="login-button" style={{
          backgroundImage: `url('/images/registerButton.png')`,
        }} onClick={() => loginWithRedirect({ screen_hint: 'signup' })}>
        Register
      </button>
    </div>
  );
};

export default RegisterPage;
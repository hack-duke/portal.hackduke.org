import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { Navigate } from "react-router-dom";
import { HeroBackground } from "../components/HeroBackground";
import { useEffect, useState } from "react";
import Button from "../components/Button";
import "./LoginPage.css";
import Countdown from "react-countdown";
import CountdownRenderer from "../components/CountdownRenderer";
import { EVENT_INFO } from "../portal/eventInfo";

const LoginPage = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();
  const [priorityCompleted, setPriorityCompleted] = useState(false);

  useEffect(() => {
    document.body.style.overflow = "hidden";
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/info" replace />;
  }

  return (
    <>
      <div className="hero">
        <HeroBackground />

        <h1 className="hero-text">Portal</h1>
        <div className="buttons-container">
          <Button
            className="hero-button"
            onClick={() => loginWithRedirect({ screen_hint: "signup" })}
          >
            Participant
          </Button>
          <Button
            className="mentor-button"
            variant="secondary"
            onClick={() =>
              window.open("https://forms.gle/iE2HH3dAPe3ubKwdA", "_blank")
            }
          >
            Mentor/Judge
          </Button>
        </div>
        {!priorityCompleted && (
          <Countdown
            date={new Date(EVENT_INFO.priorityDeadline)}
            onComplete={() => setPriorityCompleted(true)}
            renderer={({ days, hours, minutes, seconds }) => (
              <CountdownRenderer
                days={days}
                hours={hours}
                minutes={minutes}
                seconds={seconds}
                deadlineType="Priority applications"
              />
            )}
          />
        )}

        {priorityCompleted && (
          <Countdown
            date={new Date(EVENT_INFO.finalDeadline)}
            renderer={({ days, hours, minutes, seconds }) => (
              <CountdownRenderer
                days={days}
                hours={hours}
                minutes={minutes}
                seconds={seconds}
                deadlineType="Regular applications"
              />
            )}
          />
        )}
      </div>
    </>
  );
};

export default LoginPage;

import React from "react";
import NavbarComp from "../components/YourComponent";
import "./YourNewPage.css"; // optional external stylesheet

function YourNewPage() {
  const headerStyle = {
    color: "#4CAF50",
  };

  return (
    <div>
      <NavbarComp />

      <main className="about-row">
        <div className="about-box image-box">
          <img
            src="https://i.postimg.cc/8PWfcPHx/IMG-1368.jpg"
            alt="Bryan left"
          />
        </div>

        <div className="about-box about-container">
          <h1 style={headerStyle}>I’m Bryan.</h1>
          <p>
            I'm from Arlington, Texas. It's where the Dallas Cowboys and the
            Texas Rangers play but they don't tell you that.
          </p>
          <p>
            I love playing basketball, listening to rap, pop bangers, and lowkey
            a lot of other things, and clip farming.
          </p>
        </div>

        <div className="about-box image-box">
          <img
            src="https://i.postimg.cc/Dw6Z4Wb6/IMG-7590.jpg"
            alt="Bryan right"
          />
        </div>
      </main>
    </div>
  );
}

export default YourNewPage;

import React from "react";
import "./YourNewPage.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-logo">HackDuke</div>
      <ul className="navbar-links">
        <li>
          <a href="#about">About</a>
        </li>
        <li>
          <a href="#photos">Photos</a>
        </li>
        <li>
          <a href="#contact">Contact</a>
        </li>
      </ul>
    </nav>
  );
}

function YourNewPage() {
  return (
    <>
      <Navbar /> {}
      <div className="new-page-container">
        <div id="about" className="new-page-content">
          <h1>hi guys im shaine?</h1>
          <div className="info-section">
            <h2>about me</h2>
            <p>
              WHERE IM FROM: i was born in beijing, china but i moved to ithaca,
              ny when i was 3<br />
              <br />
              HOBBIES: listening to music, swimming, skiing, rock climbing,
              pickle, dilly dallying, frolicking around
            </p>
          </div>
        </div>

        <div id="photos" className="new-page-content">
          <div className="photo-grid">
            <figure>
              <img
                src="/images/shaineborgor.jpeg"
                alt="Shaine eating a burger"
              />
              <figcaption>here's me eating a borgor</figcaption>
            </figure>

            <figure>
              <img
                src="/images/shainethinkingmonkey.jpeg"
                alt="Thinking monkey sticker"
              />
              <figcaption>thinking monkey sticker</figcaption>
            </figure>

            <figure>
              <img src="/images/takenoutbyhotpot.jpeg" alt="After hotpot" />
              <figcaption>when hotpot beat me to a pulp</figcaption>
            </figure>

            <figure>
              <img src="/images/takenoutbysushi.jpeg" alt="After sushi" />
              <figcaption>when ayce sushi beat me to a pulp</figcaption>
            </figure>
          </div>
        </div>
      </div>
    </>
  );
}

export default YourNewPage;

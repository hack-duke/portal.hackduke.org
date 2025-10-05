import React from "react";
import "./NavbarComp.css";

function NavbarComp() {
  const goHome = () => {
    window.location.href = "/"; // reloads to home URL
  };

  return (
    <>
      <nav className="navbar">
        <div className="logo" onClick={goHome}>
          HackDuke
        </div>
        <ul className="nav-links">
          <li>
            <a href="#home">Home</a>
          </li>
          <li>
            <a href="#about">About Me</a>
          </li>
          <li>
            <a href="#projects">Projects</a>
          </li>
          <li>
            <a href="#contact">Contact</a>
          </li>
        </ul>
      </nav>
    </>
  );
}

export default NavbarComp;

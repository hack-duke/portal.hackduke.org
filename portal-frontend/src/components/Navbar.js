import React from "react";
import { Logo } from "./Logo";
import { Link } from "react-router-dom";
import "./Navbar.css";
import { useAuth0 } from "@auth0/auth0-react";

export const Navbar = () => {
  const { logout } = useAuth0();
  return (
    <nav className="navbar">
      <Logo />
      <div className="nav-buttons">
        <Link to="/kelly" className="nav-button">
          About Kelly 
        </Link>
        <Link to="/" className="nav-button">
          application
        </Link>
        <a
          href="https://2025.hackduke.org/"
          className="nav-button"
          target="_blank"
          rel="noopener noreferrer"
        >
          event
        </a>
        <span
          onClick={() =>
            logout({ logoutParams: { returnTo: window.location.origin } })
          }
          className="nav-button"
        >
          log out
        </span>
      </div>
    </nav>
  );
};

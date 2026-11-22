import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import "./Navbar.css";

export const Navbar = () => {
  const { logout } = useAuth0();
  return (
    <nav className="navbar" aria-label="Main navigation">
      <NavLink to="/application" className="navbar-brand">
        <span className="navbar-logo">
          <img src="/images/Small Logo.svg" alt="" />
        </span>
        <span className="navbar-wordmark">
          HackDuke <span className="navbar-wordmark-sub">Portal</span>
        </span>
      </NavLink>
      <div className="nav-buttons">
        <NavLink to="/application" className="nav-button">
          Application
        </NavLink>
        <a
          href="https://2027.hackduke.org/"
          className="nav-button"
          target="_blank"
          rel="noopener noreferrer"
        >
          Event <span aria-hidden="true">↗</span>
        </a>
        <button
          type="button"
          onClick={() =>
            logout({ logoutParams: { returnTo: window.location.origin } })
          }
          className="nav-logout"
        >
          Log out
        </button>
      </div>
    </nav>
  );
};

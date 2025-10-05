import React, { useState } from "react";
import { Logo } from "./Logo";
import { Link } from "react-router-dom";
import "./Navbar.css";
import { useAuth0 } from "@auth0/auth0-react";

export const Navbar = () => {
  const { logout } = useAuth0();
  const [open, setOpen] = useState(false);

  return (
    <nav className={`navbar ${open ? "open" : ""}`}>
      <div className="navbar-inner">
        <Logo />

        <button
          className={`hamburger ${open ? "is-active" : ""}`}
          aria-label="Toggle navigation"
          onClick={() => setOpen((s) => !s)}
        >
          <span />
          <span />
          <span />
        </button>

        <div className="nav-buttons">
          <Link to="/" className="nav-button" onClick={() => setOpen(false)}>
            application
          </Link>
          <a
            href="https://2025.hackduke.org/"
            className="nav-button"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
          >
            event
          </a>
          <button
            className="nav-button"
            onClick={() =>
              logout({ logoutParams: { returnTo: window.location.origin } })
            }
          >
            log out
          </button>
        </div>
      </div>
    </nav>
  );
};

import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import classNames from "classnames";
import { WhiteBackground } from "../WhiteBackground";
import { EVENT_INFO } from "../../portal/eventInfo";
import {
  InfoIcon,
  ClipboardIcon,
  ExternalIcon,
  LogoutIcon,
  MenuIcon,
  CloseIcon,
} from "./icons";
import "./PortalLayout.css";

// Applicant-facing shell: a sidebar on desktop that collapses into a top bar
// with a dropdown menu on small screens. Admin pages keep the regular Navbar.
const NAV_ITEMS = [
  {
    to: "/application",
    label: "Application",
    icon: ClipboardIcon,
    match: ["/application", "/form", "/status"],
  },
  { to: "/info", label: "Information", icon: InfoIcon, match: ["/info"] },
];

export const PortalLayout = ({ children }) => {
  const { logout } = useAuth0();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Close the mobile menu whenever the route changes.
  useEffect(() => setMenuOpen(false), [pathname]);

  return (
    <div className="portal">
      <WhiteBackground />
      <aside
        className={classNames("portal-sidebar", { "menu-open": menuOpen })}
      >
        <div className="portal-sidebar-top">
          <Link to="/application" className="portal-brand">
            <svg
              className="portal-brand-logo"
              viewBox="0 0 68 67"
              aria-hidden="true"
            >
              <path
                d="M66.5013 66L54.0719 66L46.9309 48.5822L46.9282 48.5757L34.9225 19.8741L33.9963 17.6597L33.0764 19.8767L21.1686 48.5738L21.1668 48.5783L13.8386 66L1.49868 66L28.5204 1L39.4796 1L66.5013 66Z"
                fill="currentColor"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
            <span className="portal-brand-text">
              HackDuke <span>Portal</span>
            </span>
          </Link>
          <button
            type="button"
            className="portal-menu-toggle"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            aria-controls="portal-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <CloseIcon /> : <MenuIcon />}
          </button>
        </div>

        <nav id="portal-nav" className="portal-nav" aria-label="Portal">
          <div className="portal-nav-group">
            <p className="portal-nav-heading">{EVENT_INFO.shortName}</p>
            {NAV_ITEMS.map(({ to, label, icon: Icon, match }) => {
              const active = match.some((m) => pathname.startsWith(m));
              return (
                <Link
                  key={to}
                  to={to}
                  className={classNames("portal-nav-link", { active })}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon />
                  {label}
                </Link>
              );
            })}
            <a
              href={EVENT_INFO.eventSiteUrl}
              className="portal-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalIcon />
              Event Site
            </a>
          </div>

          <div className="portal-nav-group portal-nav-account">
            <p className="portal-nav-heading">Account</p>
            <button
              type="button"
              className="portal-nav-link"
              onClick={() =>
                logout({ logoutParams: { returnTo: window.location.origin } })
              }
            >
              <LogoutIcon />
              Log out
            </button>
          </div>
        </nav>
      </aside>

      {menuOpen && (
        <div
          className="portal-scrim"
          aria-hidden="true"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <main className="portal-main">{children}</main>
    </div>
  );
};

export default PortalLayout;

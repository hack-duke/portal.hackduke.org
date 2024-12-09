import React from 'react';
import { Logo } from './Logo';
import { Link } from 'react-router-dom';
import './Navbar.css';
import { useAuth0 } from '@auth0/auth0-react';

export const Navbar = () => {
  const { logout } = useAuth0();
  return (
    <nav className='navbar'>
      <Logo />
      <div className='nav-buttons'>
        <Link to='/' className='nav-button'>application</Link>
        <Link onClick={() => logout({ returnTo: window.location.origin })} className='nav-button'>log out</Link>
      </div>
    </nav>
  );
};

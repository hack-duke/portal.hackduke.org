import React from 'react';
import { Logo } from './Logo';
import './Navbar.css';

export const Navbar = () => {
  return (
    <nav className='navbar'>
      <Logo/>
    </nav>
  );
};
import React from 'react';
import '../App.css';
import { useEffect } from "react";

import './WhiteBackground.css';

export const WhiteBackground = () => {
  let l1;

  const parallax = (clientX, clientY) => {
    if (!l1) {
      l1 = document.getElementById("white-bg-full");
    }
    const x = (clientX - l1.offsetLeft) / 100;
    const y = (clientY - l1.offsetTop) / 100;

    const parent = document.querySelector(":root");
    parent.style.setProperty("--x", x);
    parent.style.setProperty("--y", y);
  };

  useEffect(() => {
    function updateMouse(e) {
      e.preventDefault();
      parallax(e.clientX, e.clientY);
    }
    window.addEventListener("mousemove", updateMouse);
    return () => window.removeEventListener("mousemove", updateMouse);
  });

  return (
    <div class="white-bg-frame">
      <img className='white-bg-full' id="white-bg-full" src='/images/white-bg-full.svg' alt="Repeating White Background" />
      {/* Export the entire frame from Figma as an SVG */}
    </div>
  )
};

export default WhiteBackground;
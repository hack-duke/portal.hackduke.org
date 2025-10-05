import React from "react";
import { Navbar } from "../components/Navbar";
import KellyHobbyCard from "../components/KellyHobbyCard";
import "./KellyPage.css";

const KellyPage = () => {
    const hobbies = [
        { image: "images/kelly-arts-crafts.jpg", label: "Arts & Crafts" },
        { image: "images/kelly-trinkets.webp", label: "Buying Trinkets" },
        { image: "images/kelly-screentime.png", label: "Too much screentime" },
        { image: "images/kelly-anime.jpg", label: "Watching anime" },
        { image: "images/kelly-matcha.png", label: "Making drinks" },
        { image: "images/kelly-concert.jpg", label: "Going to concerts" },
    ];

  return (
    <div>
      <Navbar />
      <main className="page-content">
         <h1>About Kelly!!!</h1>
      <div className="upper-container">
        <img
            src = "images/kelly-header.png"
            alt = "Kelly"
        />
            <div>
            <h3>Info</h3>
            <ul>
                <li>📍 From Bridgewater, NJ (30 mins from Edison/Rutgers area) </li>
                <li>🎓 Class of 2026, CS Major + Software Systems Concentration</li>
            </ul>
            </div>
       </div>
    </main>
    
    <div className="hobbies-section">
    <h3>Hobbies</h3>
    <div className="hobby-grid">
          {hobbies.map((hobby, index) => (
            <KellyHobbyCard
              key={index}
              image={hobby.image}
              label={hobby.label}
            />
          ))}
        </div>
    </div> 
    </div>
  );
}

export default KellyPage;
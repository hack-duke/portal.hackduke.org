import React from "react";
import "./KellyHobbyCard.css";

const KellyHobbyCard = ({ image, label }) => {
  return (
    <div className="hobby-item">
      <img src={image} alt={label} />
      <div className="overlay">
        <span>{label}</span>
      </div>
    </div>
  );
};
export default KellyHobbyCard

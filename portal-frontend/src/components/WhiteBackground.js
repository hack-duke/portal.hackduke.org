import React from "react";
import "./WhiteBackground.css";

// Static, fixed backdrop: soft brand tints plus a few hackduke.org shapes
// peeking in from the edges. No scroll/mouse listeners, so it never janks.
const SHAPES = [
  { src: "/images/blob.svg", className: "bg-shape bg-shape-blob" },
  { src: "/images/triangle.svg", className: "bg-shape bg-shape-triangle" },
  { src: "/images/hexagon.svg", className: "bg-shape bg-shape-hexagon" },
  { src: "/images/oval.svg", className: "bg-shape bg-shape-oval" },
  { src: "/images/circle.svg", className: "bg-shape bg-shape-circle" },
  { src: "/images/blob_small.svg", className: "bg-shape bg-shape-blob-small" },
];

export const WhiteBackground = () => (
  <div className="white-bg-frame" aria-hidden="true">
    {SHAPES.map((shape) => (
      <img key={shape.src} src={shape.src} className={shape.className} alt="" />
    ))}
  </div>
);

export default WhiteBackground;

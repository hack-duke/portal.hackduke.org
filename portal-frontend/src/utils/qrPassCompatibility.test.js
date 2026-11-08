import React from "react";
import { QRCodeSVG } from "qrcode.react";
import jsQR from "jsqr";
const { renderToStaticMarkup } = require("react-dom/server.node");

test.each(["M", "H"])(
  "the attendee QR renderer round-trips through the real scanner decoder at level %s",
  (level) => {
    const pass = "evt_opaque_synthetic_pass_for_scanner_test";
    const svg = renderToStaticMarkup(
      React.createElement(QRCodeSVG, {
        value: pass,
        level,
        includeMargin: true,
      }),
    );
    const modules = Number(svg.match(/viewBox="0 0 (\d+) /)[1]);
    const path = svg.match(/fill="#000000" d="([^"]+)"/)[1];
    // Rasterize the renderer's horizontal SVG module runs into a camera frame.
    const scale = 5;
    const size = modules * scale;
    const pixels = new Uint8ClampedArray(size * size * 4).fill(255);
    const runs = [...path.matchAll(/M(\d+)[ ,]+(\d+)\s*h(\d+)v1H\d+z/g)];
    expect(runs.length).toBe((path.match(/M/g) || []).length);
    for (const [, x, y, length] of runs) {
      for (let row = Number(y) * scale; row < (Number(y) + 1) * scale; row++) {
        for (
          let col = Number(x) * scale;
          col < (Number(x) + Number(length)) * scale;
          col++
        ) {
          const index = (row * size + col) * 4;
          pixels[index] = pixels[index + 1] = pixels[index + 2] = 0;
        }
      }
    }
    expect(jsQR(pixels, size, size)?.data).toBe(pass);
  },
);

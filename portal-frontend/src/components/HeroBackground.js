import { useEffect } from "react";
import './HeroBackground.css'

export const HeroBackground = () => {
    // state for mouse x and y position
    // const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    // let mousePos = {x: 0, y: 0}
    let l1;

    // calculate parallax effect for rectangle
    const parallax = (clientX, clientY) => {
        if (!l1) {
            l1 = document.getElementById("hero-bg-1");
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
            // setMousePos({ x: e.clientX, y: e.clientY });
            // mousePos = { x: e.clientX, y: e.clientY }
            parallax(e.clientX, e.clientY);
            // console.log(mousePos);
        }
        l1 = document.getElementById("hero-bg-1");
        // add event listener
        window.addEventListener("mousemove", updateMouse);
        // parallax();
        // remove event listener on cleanup
        return () => window.removeEventListener("mousemove", updateMouse);
    });

    return (
        <>
            <div className="hero-bg">
                <div id="hero-bg-1">
                    <img
                        id="hero-bg-rectangle"
                        src="/images/rectangle.svg"
                        style={{ top: "20vh", left: "10vw", width: "130px" }}
                    />
                    <img
                        id="hero-bg-circle"
                        className="hero-bg-hidden"
                        src="/images/circle.svg"
                        style={{ top: "80vh", left: "40vw", width: "80px" }}
                    />
                    <img
                        id="hero-bg-blob-small"
                        src="/images/blob_small.svg"
                        style={{ top: "30vh", left: "92vw", width: "160px" }}
                    />
                </div>
                <div id="hero-bg-2">
                    <img
                        id="hero-bg-rectangle-star"
                        src="/images/rectangle_star.svg"
                        style={{ top: "20vh", left: "10vw", width: "50px" }}
                    />
                    <img
                        id="hero-bg-circle-triangle"
                        className="hero-bg-hidden"
                        src="/images/circle_triangle.svg"
                        style={{ top: "75vh", left: "40vw", width: "50px" }}
                    />
                    <img
                        id="hero-bg-plus"
                        src="/images/plus.svg"
                        style={{ top: "15vh", left: "80vw", width: "50px" }}
                    />
                </div>
                <div id="hero-bg-3">
                    <img id="hero-bg-blob" src="/images/blob.svg" />
                    <img
                        id="hero-bg-hexagon"
                        src="/images/hexagon.svg"
                        style={{ top: "50vh", left: "75vw", width: "250px" }}
                    />
                </div>
                <div id="hero-bg-4">
                    <img
                        id="hero-bg-blob-square"
                        className="hero-bg-hidden"
                        src="/images/blob_square.svg"
                        style={{ top: "85vh", left: "10vw", width: "50px" }}
                    />
                    <img
                        id="hero-bg-squiggle"
                        className="hero-bg-hidden"
                        src="/images/squiggle.svg"
                        style={{ top: "60vh", left: "60vw", width: "150px" }}
                    />
                    <img
                        id="hero-bg-hexagon-d"
                        src="/images/hexagon_d.svg"
                        style={{ top: "70vh", left: "80vw", width: "50px" }}
                    />
                </div>
                <div id="hero-bg-5">
                    <img
                        id="hero-bg-triangle"
                        src="/images/triangle.svg"
                        style={{ top: "35vh", left: "76vw", width: "450px" }}
                    />
                    <img
                        id="hero-bg-oval"
                        className="hero-bg-hidden"
                        src="/images/oval.svg"
                        style={{ top: "50vh", left: "-15vw", width: "350px" }}
                    />
                </div>
                <div id="hero-bg-6">
                    <img
                        id="hero-bg-blob-circle"
                        className="hero-bg-hidden"
                        src="/images/blob_circle.svg"
                        style={{ top: "55vh", left: "6vw", width: "50px" }}
                    />
                    <img
                        id="hero-bg-asterisk"
                        src="/images/asterisk.svg"
                        style={{ top: "87vh", left: "53vw", width: "50px" }}
                    />
                </div>
            </div>
        </>
    );
}

export default HeroBackground;

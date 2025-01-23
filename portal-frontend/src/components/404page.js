import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WhiteBackground from './WhiteBackground';
import { Navbar } from './Navbar';
import './404page.css';

const countdownLength = 5;

const NotFound = () => {
    const navigate = useNavigate();
    const [countdown, setCountdown] = useState(countdownLength); // Initial countdown value

    useEffect(() => {
        const interval = setInterval(() => {
            setCountdown((prev) => prev - 1);
        }, 1000);

        const timer = setTimeout(() => {
            navigate('/');
        }, countdownLength * 1000);

        return () => {
            clearInterval(interval); // Clean up interval
            clearTimeout(timer);     // Clean up timeout
        };
    }, [navigate]);

    return (
        <div className='building-container'>
			      <img className='building' src='/images/building.svg' alt="Building Graphic" />
						<h1 className='notfound-title'>404</h1>
            <p className='notfound-desc'>Page Not Found: {countdown}</p>
        </div>
    );
}

export default NotFound;

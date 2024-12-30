import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WhiteBackground from './WhiteBackground';
import { Navbar } from './Navbar';

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
        <div>
            <Navbar/>
            <WhiteBackground/>
            <h1 style={{
                textAlign: 'center',
                marginTop: '20vh',
                fontSize: '3em',
            }}>404 - Not Found!</h1>
            <p style={{
                textAlign: 'center',
                fontSize: '1.5em',
            }}>Redirecting to home in {countdown} second{countdown !== 1 ? 's' : ''}...</p>
        </div>
    );
}

export default NotFound;

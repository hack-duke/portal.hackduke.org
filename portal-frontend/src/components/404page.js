import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
    const navigate = useNavigate();
    const [countdown, setCountdown] = useState(3); // Initial countdown value

    useEffect(() => {
        const interval = setInterval(() => {
            setCountdown((prev) => prev - 1);
        }, 1000);

        const timer = setTimeout(() => {
            navigate('/');
        }, 3000);

        return () => {
            clearInterval(interval); // Clean up interval
            clearTimeout(timer);     // Clean up timeout
        };
    }, [navigate]);

    return (
        <div>
            <h1>404 - Not Found!</h1>
            <p>Redirecting to home in {countdown} second{countdown !== 1 ? 's' : ''}...</p>
        </div>
    );
}

export default NotFound;

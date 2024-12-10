import './NextButton.css'
import { useState } from 'react';
import classNames from 'classnames';

export const NextButton = ({onClick, disabled, ...props}) => {
    const [isVibrating, setIsVibrating] = useState(false);

    const handleClick = () => {
        if (disabled) {
            setIsVibrating(true);
            setTimeout(() => setIsVibrating(false), 400);
        }
        onClick(); 
    };

    const containerClass = classNames('next-container', {
        vibrate: isVibrating,
    });

    return (
        <div className={containerClass} onClick={handleClick} {...props}> 
            <div className='next-text'>Next</div>
            <img className="next-icon" src="/images/Right Arrow.svg" alt="Next Button" />
        </div>
    );
};

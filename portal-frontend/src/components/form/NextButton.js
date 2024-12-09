import './NextButton.css'

export const NextButton = (props) => {
    return (
        <div className='next-container' {...props}> 
            <div className='next-text'>Next</div>
            <img className="next-icon" src="/images/Right Arrow.svg" alt="Next Button" />
        </div>
    );
};

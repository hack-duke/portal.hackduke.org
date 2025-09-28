const CountdownRenderer = ({ days, hours, minutes, seconds }) => {
  return (
    <div className="hero-countdown">
      <p>
        Due in {days} days {hours} hours {minutes} minutes {seconds} seconds
      </p>
    </div>
  );
};

export default CountdownRenderer;

import "./BackButton.css";

export const BackButton = ({ onClick, ...props }) => {
  return (
    <div className="back-container" onClick={onClick} {...props}>
      <img
        className="back-icon"
        src="/images/Left Arrow.svg"
        alt="Back Button"
      />
      <div className="back-text">Back</div>
    </div>
  );
};

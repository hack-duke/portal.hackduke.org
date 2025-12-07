import "./MultipleChoiceQuestion.css";
import React, { forwardRef, useImperativeHandle } from "react";

// eslint-disable-next-line react/prop-types
export const MultipleChoiceQuestion = forwardRef((props, ref) => {
  const {
    name,
    label,
    options,
    formData,
    handleInputChange,
    required = false,
    firstTry,
    isValid = (value) => !required || (value && value.trim() !== ""),
  } = props;

  useImperativeHandle(ref, () => ({
    isValid: () => isValid(formData[name]),
  }));

  return (
    <div className="multiple-choice-container">
      <label className="mc-label">
        {label}
        {required && "*"}
      </label>
      <div className="mc-options">
        {options.map((option) => (
          <label key={option} className="mc-option">
            <input
              type="radio"
              name={name}
              value={option}
              checked={formData[name] === option}
              onChange={(e) => handleInputChange(name, e.target.value)}
              required={required}
            />
            <span>{option}</span>
          </label>
        ))}
      </div>
      {!firstTry && !isValid(formData[name]) && (
        <div className="error-message">This field is required</div>
      )}
    </div>
  );
});

MultipleChoiceQuestion.displayName = "MultipleChoiceQuestion";

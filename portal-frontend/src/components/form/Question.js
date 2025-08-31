import "./Question.css";
import React, { forwardRef, useImperativeHandle } from "react";
import classNames from "classnames";

export const Question = forwardRef(
  (
    {
      name,
      label,
      type = "text",
      formData,
      handleInputChange,
      required = false,
      placeholder,
      firstTry,
      isValid = (value) => !required || (value && value.trim() !== ""),
    },
    ref,
  ) => {
    // Default validation function

    useImperativeHandle(ref, () => ({
      isValid: () => isValid(formData[name]),
    }));

    console.log(isValid(formData[name]));

    return (
      <div className="question-container">
        <label className="question-label" htmlFor={name}>
          {label}
          {required && "*"}
        </label>
        <input
          className={classNames("question-input", {
            "invalid-border": !firstTry && !isValid(formData[name]),
          })}
          type={type}
          id={name}
          name={name}
          value={formData[name] || ""}
          onChange={(e) => handleInputChange(name, e.target.value)}
          placeholder={placeholder}
          required
        />
      </div>
    );
  },
);

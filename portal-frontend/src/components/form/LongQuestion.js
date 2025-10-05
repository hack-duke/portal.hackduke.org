import "./LongQuestion.css";
import classNames from "classnames";
import React, { forwardRef, useImperativeHandle } from "react";

export const LongQuestion = forwardRef(
  (
    {
      name,
      label,
      formData,
      handleInputChange,
      rows,
      required = false,
      firstTry,
      isValid = (value) => !required || (value && value.trim() !== ""),
    },
    ref,
  ) => {
    useImperativeHandle(ref, () => ({
      isValid: () => isValid(formData[name]),
    }));

    return (
      <div className="long-container">
        <label className="long-label" htmlFor={name}>
          {label}
          {required && "*"}
        </label>
        <textarea
          className={classNames("long-textarea", {
            "invalid-border": !firstTry && !isValid(formData[name]),
          })}
          id={name}
          name={name}
          value={formData[name] || ""}
          onChange={(e) => handleInputChange(name, e.target.value)}
          rows={rows}
          required
        />
      </div>
    );
  },
);

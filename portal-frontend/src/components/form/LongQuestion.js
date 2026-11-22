import "./LongQuestion.css";
import classNames from "classnames";
import React, { forwardRef, useImperativeHandle } from "react";

const countWords = (value) =>
  value && value.trim() ? value.trim().split(/\s+/).length : 0;

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
      maxWords,
      isValid = (value) =>
        (!required || (value && value.trim() !== "")) &&
        (!maxWords || countWords(value) <= maxWords),
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
        {maxWords && (
          <span
            className={classNames("long-word-count", {
              "long-word-count-over": countWords(formData[name]) > maxWords,
            })}
          >
            {countWords(formData[name])} / {maxWords} words
          </span>
        )}
      </div>
    );
  },
);

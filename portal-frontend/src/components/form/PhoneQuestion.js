import "./Question.css";
import React, { forwardRef, useImperativeHandle } from "react";
import classNames from "classnames";

const US_PHONE = /^\d{3}-\d{3}-\d{4}$/;
// "+" country code then 7–14 more digits, optionally separated by spaces or dashes.
const INTL_PHONE = /^\+\d{1,3}([ -]?\d){6,14}$/;

export const isValidPhone = (value) =>
  !!value && (US_PHONE.test(value) || INTL_PHONE.test(value.trim()));

// US/Canada numbers are auto-formatted as 123-456-7890 while typing.
// Numbers starting with "+" are treated as international and left as typed.
const formatPhone = (raw) => {
  if (raw.trim().startsWith("+")) {
    return "+" + raw.replace(/[^\d -]/g, "").replace(/^[ -]+/, "");
  }
  const digits = raw.replace(/\D/g, "").slice(0, 10);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
};

export const PhoneQuestion = forwardRef(
  (
    {
      name,
      label,
      formData,
      handleInputChange,
      required = false,
      firstTry,
      isValid = (value) => (!required && !value) || isValidPhone(value),
    },
    ref,
  ) => {
    useImperativeHandle(ref, () => ({
      isValid: () => isValid(formData[name]),
    }));

    const invalid = !firstTry && !isValid(formData[name]);

    return (
      <div className="question-container">
        <label className="question-label" htmlFor={name}>
          {label}
          {required && <span className="required-mark">*</span>}
        </label>
        <input
          className={classNames("question-input", {
            "invalid-border": invalid,
          })}
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          id={name}
          name={name}
          value={formData[name] || ""}
          onChange={(e) => handleInputChange(name, formatPhone(e.target.value))}
          placeholder="123-456-7890"
        />
        <span
          className={classNames("question-hint", {
            "question-hint-error": invalid,
          })}
        >
          {invalid
            ? "Use 123-456-7890, or start with + and your country code."
            : "Outside the US? Start with + and your country code."}
        </span>
      </div>
    );
  },
);

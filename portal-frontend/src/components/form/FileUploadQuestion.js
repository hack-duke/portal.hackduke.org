import "./FileUploadQuestion.css";
import React, { forwardRef, useImperativeHandle } from "react";
import classNames from "classnames";

export const FileUploadQuestion = forwardRef(
  (
    {
      name,
      label,
      accept,
      formData,
      handleFileChange,
      required = false,
      firstTry,
      isValid = (value) => !required || value,
    },
    ref,
  ) => {
    useImperativeHandle(ref, () => ({
      isValid: () => isValid(formData[name]), // Is this the best way to validate?
    }));

    const file = formData?.[name];

    return (
      <div className="file-question">
        <span className="question-label">
          {label}
          {required && <span className="required-mark">*</span>}
        </span>
        <label
          htmlFor={name}
          className={classNames("file-dropzone", {
            "file-dropzone-filled": file,
            "invalid-border": !firstTry && !isValid(file),
          })}
        >
          <input
            id={name}
            type="file"
            accept={accept}
            onChange={(e) => handleFileChange(name, e.target.files[0])}
            required={required}
          />
          <span className="file-dropzone-icon" aria-hidden="true">
            {file ? "✓" : "↑"}
          </span>
          <span className="file-dropzone-text">
            <strong>{file ? file.name : "Choose a file"}</strong>
            <span>{file ? "Click to replace" : "PDF only"}</span>
          </span>
        </label>
      </div>
    );
  },
);

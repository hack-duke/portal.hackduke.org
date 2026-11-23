import React, { useState, useRef, useEffect } from "react";
import "./SinglePageForm.css";

// Renders every <Page> as a section of one continuously scrolling form.
// Validation errors are hidden until the applicant first tries to submit;
// after that, invalid fields are highlighted and the view jumps to the first one.
export const SinglePageForm = ({ onSubmit, children }) => {
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [scrollRequest, setScrollRequest] = useState(0);
  const sectionRefs = useRef([]);

  const sections = React.Children.toArray(children);

  useEffect(() => {
    if (scrollRequest === 0) return;
    const firstInvalidField = document.querySelector(".invalid-border");
    const firstInvalidSection = sectionRefs.current.find(
      (section) => section && !section.isPageValid(),
    );
    const target = firstInvalidField || firstInvalidSection?.element;
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      if (typeof target.focus === "function") {
        target.focus({ preventScroll: true });
      }
    }
  }, [scrollRequest]);

  const isFormValid = () =>
    sectionRefs.current
      .slice(0, sections.length)
      .every((section) => !section || section.isPageValid());

  const handleSubmit = async () => {
    if (!isFormValid()) {
      setShowErrors(true);
      setScrollRequest((n) => n + 1);
      return;
    }
    setLoading(true);
    try {
      await onSubmit(formData);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (name, file) => {
    setFormData((prev) => ({ ...prev, [name]: file }));
  };

  return (
    <div className="single-page-form">
      {sections.map((child, index) =>
        React.cloneElement(child, {
          formData,
          handleInputChange,
          handleFileChange,
          firstTry: !showErrors,
          sectionNumber: index + 1,
          ref: (el) => (sectionRefs.current[index] = el),
        }),
      )}
      <div className="submit-container">
        {showErrors && !isFormValid() && (
          <p className="form-error-summary">
            Please fill out all required fields highlighted above.
          </p>
        )}
        <button
          type="button"
          className="submit-button"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "Submitting…" : "Submit application"}
        </button>
        <p className="submit-hint">
          You can only submit once, so double-check your answers.
        </p>
      </div>
    </div>
  );
};

import React, { forwardRef, useImperativeHandle, useRef } from "react";
import "./Page.css";

export const Page = forwardRef(
  (
    {
      children,
      title,
      formData,
      handleInputChange,
      handleFileChange,
      firstTry,
      sectionNumber,
    },
    ref,
  ) => {
    const questionRefs = useRef([]);
    const containerRef = useRef(null);

    const childrenWithProps = React.Children.map(children, (child, index) => {
      return React.cloneElement(child, {
        formData,
        handleInputChange,
        handleFileChange,
        firstTry,
        ref: (el) => (questionRefs.current[index] = el),
      });
    });

    useImperativeHandle(ref, () => ({
      isPageValid: () => {
        // If we want to we can customize this too for each page
        return questionRefs.current.every((question) =>
          question?.isValid ? question.isValid() : true,
        );
      },
      get element() {
        return containerRef.current;
      },
    }));

    return (
      <section className="page-container" ref={containerRef}>
        {title && (
          <header className="page-header">
            {sectionNumber && (
              <span className="page-number" aria-hidden="true">
                {String(sectionNumber).padStart(2, "0")}
              </span>
            )}
            <h2 className="page-title">{title}</h2>
          </header>
        )}
        <div className="page-fields">{childrenWithProps}</div>
      </section>
    );
  },
);

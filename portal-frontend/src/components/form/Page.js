    import React, {forwardRef, useImperativeHandle, useRef} from "react";
    import './Page.css';

    export const Page = forwardRef(({ children, title, formData, handleInputChange, handleFileChange, firstTry}, ref) => {
        const questionRefs = useRef([]);
        
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
            isPageValid: () => { // If we want to we can customize this too for each page
                return questionRefs.current.every((question) =>
                    question?.isValid ? question.isValid() : true
                );
            },
        }));

        return (
        <div className="page-container">
            <h1 className="page-title">{title}</h1>
            {childrenWithProps}
        </div>);
    });

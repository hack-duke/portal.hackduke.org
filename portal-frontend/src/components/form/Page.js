    import React, {forwardRef, useImperativeHandle, useRef} from "react";
    import './Page.css';
    import classNames from "classnames";

    export const Page = forwardRef(({ children, title, formData, handleInputChange, handleFileChange}, ref) => {
        const questionRefs = useRef([]);
        
        const childrenWithProps = React.Children.map(children, (child, index) => {
            return React.cloneElement(child, {
                formData,
                handleInputChange,
                handleFileChange,
                ref: (el) => (questionRefs.current[index] = el),
            });
        });

        useImperativeHandle(ref, () => ({
            isPageValid: () => {
                return questionRefs.current.every((question) =>
                    question?.isValid ? question.isValid() : true
                );
            },
        }));

        return (
        <div>
            <h1 className="page-title">{title}</h1>
            {childrenWithProps}
        </div>);
    });

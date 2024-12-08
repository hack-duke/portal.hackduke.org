import React from "react";

export const Page = ({ children, formData, handleInputChange, handleFileChange }) => {
    const childrenWithProps = React.Children.map(children, child => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
        });
    });

    return <div>{childrenWithProps}</div>;
}

import React from "react";
import './Page.css';

export const Page = ({ children, title, formData, handleInputChange, handleFileChange }) => {
    const childrenWithProps = React.Children.map(children, child => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
        });
    });

    return (
    <div>
        <h1 className="page-title">{title}</h1>
        {childrenWithProps}
    </div>);
}

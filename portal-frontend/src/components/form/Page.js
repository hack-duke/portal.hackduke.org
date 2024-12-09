import React from "react";

export const Page = ({ children, formData, handleInputChange, handleFileChange }) => {
    const childrenWithProps = React.Children.map(children, child => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
        });
    });

    return <div style={
        {
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            height: '100%',
            padding: '2rem',
            marginTop: '10rem',
        }
    }>{childrenWithProps}</div>;
}

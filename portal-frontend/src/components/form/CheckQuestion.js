import './CheckQuestion.css';
import React, { forwardRef, useImperativeHandle } from 'react';

export const CheckQuestion = forwardRef(({
    name,
    formData,
    handleInputChange,
    required = false,
    isValid = (value) => !required || value,
    children // Accept children for label content
}, ref) => {

    useImperativeHandle(ref, () => ({
        isValid: () => isValid(formData[name]),
    }));

    return (
        <div className="check-container">
            <div>
                <input
                    type="checkbox"
                    className="styled-checkbox"
                    id={name}
                    name={name}
                    checked={formData[name] || false}
                    onChange={e => handleInputChange(name, e.target.checked)}
                    required={required}
                />
                <label className="checkbox-style" htmlFor={name} />
            </div>
            <label className="check-label">
                {children}
                {required && '*'}
            </label>
        </div>
    );
});

import './Question.css';
import React, { forwardRef, useImperativeHandle } from 'react';

export const Question = forwardRef(({ 
    name, 
    label, 
    type = 'text', 
    formData, 
    handleInputChange, 
    required = false, 
    isValid = (value) => !required || (value && value.trim() !== '')}, ref) => {

    useImperativeHandle(ref, () => ({
        isValid: () => isValid(formData[name]),
    }));

    return (
        <div className="question-container">
            <label className="question-label" htmlFor={name}>{label}{required && '*'}</label>
            <input
                className="question-input"
                type={type}
                id={name}
                name={name}
                value={formData[name] || ''}
                onChange={e => handleInputChange(name, e.target.value)}
                required
            />
        </div>
    );
});

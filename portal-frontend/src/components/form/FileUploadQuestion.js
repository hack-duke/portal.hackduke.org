import './FileUploadQuestion.css'
import React, { forwardRef, useImperativeHandle } from 'react';

export const FileUploadQuestion = forwardRef(({ 
    name, 
    label, 
    accept, 
    formData, 
    handleFileChange,
    required = false, 
    isValid = (value) => !required || value}, ref) => {

    useImperativeHandle(ref, () => ({
        isValid: () => isValid(formData[name]), // Is this the best way to validate?
    }));

    return (
        <div>
            <label className="file-question-label" htmlFor={name}>{label}{required && '*'}</label>
            <label className="file-question-button" htmlFor={name}>Choose File</label>
            <input
                id={name}
                type="file"
                accept={accept}
                onChange={e => handleFileChange(name, e.target.files[0])}
                required
            />
            <span className='file-question-name'>
                {formData?.[name] && formData[name].name}
            </span>
        </div>
    );
});

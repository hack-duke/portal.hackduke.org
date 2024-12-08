// Example API

/* <MultiPageForm onSubmit={mockSubmit}>
      <Page>
        <Question name="school" label="School:" />
        <Question name="major" label="Major:" />
        <Question name="graduationYear" label="Graduation Year:" type="number" />
      </Page>
      <Page>
        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
      </Page>
</MultiPageForm> */

import React, { useState } from 'react';

const MultiPageForm = ({ onSubmit, children }) => {
    const [page, setPage] = useState(0);
    const [formData, setFormData] = useState({});
    const [loading, setLoading] = useState(false);

    console.log(page);
    console.log(children.length);

    const handleNext = () => {
        setPage(page + 1);
    }

    const handleBack = () => {
        setPage(page - 1);
    }

    const handleSubmit = async () => {
        if (page === children.length - 1) {
            setLoading(true);
            await onSubmit(formData);
            setLoading(false);
        } else {
            setPage(page + 1);
        }
    }

    const handleInputChange = (name, value) => {
        setFormData({ ...formData, [name]: value });
    }

    const handleFileChange = (name, file) => {
        setFormData({ ...formData, [name]: file });
    }

    const childrenWithProps = React.Children.map(children, child => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
        });
    });

    return (
        <div>
            {childrenWithProps[page]}
            <div>
                {page > 0 && <button onClick={handleBack}>Back</button>}
                {page < children.length - 1 && <button onClick={handleNext}>Next</button>}
                {page == children.length - 1 && <button onClick={handleSubmit} disabled={loading}>Submit</button>}
            </div>
        </div>
    );
}

const Page = ({ children, formData, handleInputChange, handleFileChange }) => {
    const childrenWithProps = React.Children.map(children, child => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
        });
    });

    return <div>{childrenWithProps}</div>;
}

const Question = ({ name, label, type = 'text', formData, handleInputChange }) => {
    return (
        <div>
            <label htmlFor={name}>{label}</label>
            <input
                type={type}
                id={name}
                name={name}
                value={formData[name] || ''}
                onChange={e => handleInputChange(name, e.target.value)}
                required
            />
        </div>
    );
}

const FileUploadQuestion = ({ name, label, accept, formData, handleFileChange }) => {
    return (
        <div>
            <label htmlFor={name}>{label}</label>
            <input
                id={name}
                type="file"
                accept={accept}
                onChange={e => handleFileChange(name, e.target.files[0])}
                required
            />
        </div>
    );
}

export { MultiPageForm, Page, Question, FileUploadQuestion };

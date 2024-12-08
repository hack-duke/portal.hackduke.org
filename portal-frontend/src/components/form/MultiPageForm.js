import { useState } from "react";
import React from "react";

export const MultiPageForm = ({ onSubmit, children }) => {
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
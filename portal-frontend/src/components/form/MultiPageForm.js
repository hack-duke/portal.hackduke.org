import { useState } from "react";
import React from "react";
import './MultiPageForm.css' // Maybe move these styles into a button component
import { BackButton } from "./BackButton";
import { NextButton } from "./NextButton";
import Button from "../Button";

export const MultiPageForm = ({ onSubmit, children }) => {
    const [page, setPage] = useState(0);
    const [formData, setFormData] = useState({});
    const [loading, setLoading] = useState(false);

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
            <div className="submit-container">
                {page === children.length - 1 && <Button className="submit-button" variant="tertiary" onClick={handleSubmit} disabled={loading}>Submit</Button>}
            </div>
            <div className="button-container">
                {page > 0 && <BackButton onClick={handleBack}/>}
                {page < children.length - 1 && <NextButton onClick={handleNext}/>}
            </div>
        </div>
    );
}
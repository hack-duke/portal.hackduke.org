import { useState, useRef, useEffect } from "react";
import React from "react";
import './MultiPageForm.css'
import { BackButton } from "./BackButton";
import { NextButton } from "./NextButton";
import Button from "../Button";

export const MultiPageForm = ({ onSubmit, children }) => {
    const [page, setPage] = useState(0);
    const [formData, setFormData] = useState({});
    const [loading, setLoading] = useState(false);
    const [isPageValid, setIsPageValid] = useState(false);
    const pageRefs = useRef([]);

    useEffect(() => {
        setIsPageValid(pageRefs.current[page]?.isPageValid() === true);
    }, [page, formData]);

    const handleNext = () => {
        if (isPageValid) {
            setPage(page + 1);
        }
    }

    const handleBack = () => {
        setPage(page - 1);
    }

    const handleSubmit = async () => {
        if (page === children.length - 1) {
            if (isPageValid) {
                setLoading(true);
                await onSubmit(formData);
                setLoading(false);
            }
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

    const childrenWithProps = React.Children.map(children,(child, index) => {
        return React.cloneElement(child, {
            formData,
            handleInputChange,
            handleFileChange,
            ref: (el) => (pageRefs.current[index] = el),
        });
    });

    return (
        <div>
            {childrenWithProps[page]}
            <div className="submit-container">
                {page === children.length - 1 && <Button className="submit-button" variant="tertiary" onClick={handleSubmit} disabled={loading || !isPageValid}>Submit</Button>}
            </div>
            <div className="button-container">
                {page > 0 && <BackButton onClick={handleBack}/>}
                {page < children.length - 1 && <NextButton onClick={handleNext} disabled={!isPageValid}/>}
            </div>
        </div>
    );
}
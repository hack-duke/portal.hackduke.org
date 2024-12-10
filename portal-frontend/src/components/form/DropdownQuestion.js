import React, { forwardRef, useImperativeHandle, useState } from 'react';
import Select, { components } from 'react-select';

const DropdownIndicator = (props) => {
  // return (
  //     <img {...props.innerProps} src='/images/DropdownIndicator.svg'/>
  // )
  return (
    <components.DropdownIndicator {...props}>
      <img src='/images/DropdownIndicator.svg' style={{ width: '1rem', fill: "#0042c6" }} />
    </components.DropdownIndicator>
  )
}

export const DropdownQuestion = forwardRef(({
  name,
  label,
  formData,
  handleInputChange,
  required = false,
  firstTry,
  isValid = (value) => !required || (value && value.trim() !== ''),
  options
}, ref) => {

  // options should be [{value: 'value', label: 'label'}]

  useImperativeHandle(ref, () => ({
    isValid: () => isValid(formData[name]),
  }))

  return (
    <div className="question-container">
      <label className="question-label" htmlFor={name}>{label}{required && '*'}</label>
      <Select
        defaultValue={formData[name]}
        onChange={({ value }) => handleInputChange(name, value)}
        options={options}
        placeholder={"Select country"}
        classNamePrefix={"dropdown"}
        classNames={{
          control: () => {return (!firstTry && !isValid(formData[name])) ? 'invalid-border question-input' : 'question-input'}
        }}
        components={{
          "DropdownIndicator": DropdownIndicator,
        }}
        name={name}
        styles={{
          indicatorSeparator: (styles) => ({ ...styles, width: '0rem' }),
          container: (styles) => ({
            ...styles, "fontFamily": "'Oxygen', sans-serif", "fontWeight": 400,
          }),
          control: (styles) => ({
            ...styles, '&:hover': {
              border: '1px solid black', // Black border on hover,
              minHeight: '0rem'
            },
            padding: "0rem 0.5rem",
            minHeight: "0rem",
          }),
          valueContainer: (styles) => ({ ...styles, padding: "0rem" }),
          input: (styles) => ({ ...styles, padding: "0rem" }),
        }}
      />

    </div>
  );
});
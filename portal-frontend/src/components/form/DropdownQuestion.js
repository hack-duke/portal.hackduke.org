import React, { useState } from 'react';
import Select, {components} from 'react-select';

const DropdownIndicator = (props) => {
    // return (
    //     <img {...props.innerProps} src='/images/DropdownIndicator.svg'/>
    // )
    return (
        <components.DropdownIndicator {...props}>
            <img src='/images/DropdownIndicator.svg' style={{width: '0.75rem'}}/>
        </components.DropdownIndicator>
    )
}

const options = [
    { value: 'chocolate', label: 'Chocolate' },
    { value: 'strawberry', label: 'Strawberry' },
    { value: 'vanilla', label: 'Vanilla' },
  ];
  
  export default function DropdownQuestion() {
    const [selectedOption, setSelectedOption] = useState(null);


    return (
      <div>
        <Select
          defaultValue={selectedOption}
          onChange={setSelectedOption}
          options={options}
          placeholder={"Select Ice Cream"}
          components={{
            "DropdownIndicator": DropdownIndicator,
          }}
          styles={{
            indicatorSeparator: (styles) => ({...styles, width: '0rem'}),
            container: (styles) => ({...styles, width: '30rem', "font-family": "'Oxygen', sans-serif", "font-weight": 400
            })}}
        />
        
      </div>
    );
  }
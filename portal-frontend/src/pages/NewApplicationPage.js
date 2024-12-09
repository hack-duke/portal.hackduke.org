import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { MultiPageForm, Page, Question, FileUploadQuestion } from '../components/form/Form'
import { Navbar } from '../components/Navbar';
import './NewApplicationPage.css'

const NewApplicationPage = () => {
    const { user, getAccessTokenSilently, logout } = useAuth0();
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(null);

    const onSubmit = async (formData) => {
        setError(null);
    
        try {
          const token = await getAccessTokenSilently();
          const submitData = new FormData();
          submitData.append('userId', user.sub);
          submitData.append('email', user.email);
          submitData.append('name', user.name);
          Object.keys(formData).forEach((fieldName) => {
            submitData.append(fieldName, formData[fieldName]);
          })
    
          const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/applications/submit`, 
            submitData,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'multipart/form-data',
              },
            }
          );

          setStatus(response.data.message);
        } catch (error) {
          console.error('Application submission error:', error);
          setError(error.response?.data?.error || 'Failed to submit application');
        }
    };
    
    return (
        <>
            <Navbar/>
            <div className='form-container'>
                <MultiPageForm onSubmit={onSubmit}> 
                    <Page title="General Information">
                        <Question name="firstName" label="First Name" />
                        <Question name="lastName" label="Last Name" />
                        <Question name="prefName" label="Preferred Name" />
                        <Question name="birthDate" label="Birth Date" />
                        <Question name="school" label="School" />
                        <Question name="graduationYear" label="Graduation Year" type="number" />
                    </Page>
                    <Page>
                        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
                    </Page>
                </MultiPageForm>
            </div>

            {error && <div style={{color: 'red'}}>{error}</div>}
            {status && <div style={{color: 'green'}}>{status}</div>}
        </>
    )
};

export default NewApplicationPage;
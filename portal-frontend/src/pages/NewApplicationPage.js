import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { MultiPageForm, Page, Question, FileUploadQuestion } from '../components/form/Form'

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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Application Submission</h2>
                <button onClick={() => logout({ returnTo: window.location.origin })}>
                Log Out
                </button>
            </div>

            <MultiPageForm onSubmit={onSubmit}> 
                <Page>
                    <Question name="school" label="School:" />
                    <Question name="major" label="Major:" />
                    <Question name="graduationYear" label="Graduation Year:" type="number" />
                </Page>
                <Page>
                    <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
                </Page>
            </MultiPageForm>
        </>
    )
};

export default NewApplicationPage;
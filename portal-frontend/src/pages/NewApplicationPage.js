import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { MultiPageForm, Page, Question, LongQuestion, FileUploadQuestion } from '../components/form/Form'
import { Navbar } from '../components/Navbar';
import './NewApplicationPage.css'
import {WhiteBackground} from '../components/WhiteBackground'
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const NewApplicationPage = () => {
    const { user, getAccessTokenSilently } = useAuth0();
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

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

    useEffect(
      () => {
        const checkIfSubmitted = async () => {
          const token = await getAccessTokenSilently();
          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/applications/application`, {
            headers: {
              "Authorization": `Bearer ${token}`
            }
          })

          if (response.status === 200) {
            navigate('/status')
          }
        }

        checkIfSubmitted()
      },
      [navigate]
    )
    
    return (
        <>
            <Navbar/>
            <WhiteBackground/>
            <div className='form-container'>
                <MultiPageForm onSubmit={onSubmit}> 
                    <Page title="General Information">
                        <Question name="firstName" label="First Name" />
                        <Question name="lastName" label="Last Name" />
                        <Question name="prefName" label="Preferred Name" />
                        <Question name="birthDate" label="Birth Date" />
                        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" />
                    </Page>
                    <Page title="Education">
                        <Question name="country" label="Country of Residence" />
                        <Question name="university" label="University Name" />
                        <Question name="major" label="Major" />
                        <Question name="graduationYear" label="Graduation Year" type="number" />
                    </Page>
                    <Page title="About You">
                        <LongQuestion name="whyhackduke" label="Tell us a bit about why you want to attend HackDuke! What do you hope to learn?" rows={5}/>
                        <LongQuestion name="track" label="Which of our four tracks excites you the most? Why?" rows={2}/>
                    </Page>
                </MultiPageForm>
                {error && <div style={{color: 'red'}}>{error}</div>}
                {status && <div style={{color: 'green'}}>{status}</div>}
            </div>
        </>
    )
};

export default NewApplicationPage;
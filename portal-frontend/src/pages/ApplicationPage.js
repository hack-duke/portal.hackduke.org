import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';
import { MultiPageForm, Page, Question, LongQuestion, FileUploadQuestion, CheckQuestion } from '../components/form/Form'
import { Navbar } from '../components/Navbar';
import './ApplicationPage.css'
import {WhiteBackground} from '../components/WhiteBackground'
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FullPageLoadingSpinner } from '../components/FullPageLoadingSpinner';
import Modal, {ModalHeader} from '../components/Modal';

const ApplicationPage = () => {
    const { user, getAccessTokenSilently } = useAuth0();
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    /* const onSubmit = async (formData) => {
        setLoading(true);
        setError(null);
        try {
          let token;
          try {
            token = await getAccessTokenSilently();
          } catch (tokenError) {
            console.error('Token error:', tokenError);
            if (tokenError.message.includes('Missing Refresh Token')) {
              openModal();
              setError('Session expired. Please try logging out and logging back in.');
              return;
            }
            throw tokenError;
          }

          const submitData = new FormData();
          submitData.append('userId', user.sub);
          submitData.append('email', user.email);
          submitData.append('name', user.name);
          Object.keys(formData).forEach((fieldName) => {
            submitData.append(fieldName, formData[fieldName]);
          });

          const response = await axios.post(
            `${process.env.REACT_APP_BACKEND_URL}/api/applications/submit`,
            submitData,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'multipart/form-data',
              },
            }
          );

          if (response.status === 201) {
            navigate('/status', { state: { firstTime: true }});
          }
        } catch (error) {
          openModal();
          console.error('Application submission error:', error);
          setError(error.response?.data?.error || 'An error occurred while submitting your application. Please try logging out and logging back in.');
        }
        setLoading(false);
    }; */

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
        setLoading(true)
        checkIfSubmitted()
        setLoading(false)
      },
      [navigate]
    )
    
    return (
        <>
            <Navbar/>
            <WhiteBackground/>
            {loading && <FullPageLoadingSpinner/>}
            <Modal isOpen={isModalOpen} onClose={closeModal}>
              <ModalHeader>Application Submission Error</ModalHeader>
              <p>{error}</p>
              <p>If this error continues to occur, please reach out to <a href='mailto:hackers@hackduke.org'>hackers@hackduke.org</a> and we will help resolve your issue promptly.</p>
            </Modal>
						<div className='notice-container'>
							<h1>Applications Closed.</h1>
  						<p>Thank you for your interest in HackDuke Code for Good. The application window has now officially closed. </p> 
							<p>If you believe there was an error with your application, please reach out to <a href='mailto:hackers@hackduke.org'>hackers@hackduke.org.</a></p> 
							<p>Stay tuned for future opportunities!</p>
						</div>
            {/* Bug: passing a non-question element as a child will break everything */}
						{/*<div className='form-container'>
                <MultiPageForm onSubmit={onSubmit}>
                    <Page title="General Information">
                        <Question name="firstName" label="First Name" required/> 
                        <Question name="lastName" label="Last Name" required/>
                        <Question name="prefName" label="Preferred Name"/>
                        <Question name="age" type="number" label="Age" required/>
                        <FileUploadQuestion name="resume" label="Upload Resume (PDF only)" accept="application/pdf" required/>
                    </Page>
                    <Page title="Education">
                        <Question name="country" label="Country of Residence" required/>
                        <Question name="university" label="University Name" required/>
                        <Question name="major" label="Major" required/>
                        <Question name="graduationYear" label="Graduation Year" type="number" placeholder="20XX" required/>
                        <Question name="phone" label="Phone Number" type="tel" placeholder="123-456-7890" required/>
                    </Page>
                    <Page title="About You">
                        <LongQuestion name="whyhackduke" label="Tell us a bit about why you want to attend HackDuke! What do you hope to learn?" rows={5} required/>
                        <LongQuestion name="whytrack" label="Which of our four tracks excites you the most? Why?" rows={2} required/>
                    </Page>
                    <Page title="Agreements">
                      <CheckQuestion name="community_agr" required>
                        I have read and agree to abide by the <a href='https://dukecommunitystandard.students.duke.edu/'>Duke Community Standard</a> during the event.
                      </CheckQuestion>
                      <CheckQuestion name="photo_agr" required>
                        I hereby grant permission for HackDuke and all official sponsors to use my photograph and or video in marketing, promotional materials, and publications, both online and in print, without compensation.
                      </CheckQuestion>
                      <CheckQuestion name="waiver_agr" required>
                        I acknowledge and assume all risks associated with participation, releasing the organizers from any liability for injury, loss, or damage.
                      </CheckQuestion>
                    </Page>
                    <Page title="Agreements (MLH)">
                      <CheckQuestion name="mlh1" required>
                        I have read and agree to the <a href='https://github.com/MLH/mlh-policies/blob/main/code-of-conduct.md'>MLH Code of Conduct</a>.
                      </CheckQuestion>
                      <CheckQuestion name="mlh2" required>
                        I authorize you to share my application/registration information with Major League Hacking for event administration, ranking, and MLH administration in-line with the <a href="https://github.com/MLH/mlh-policies/blob/main/privacy-policy.md">MLH Privacy Policy</a>. I further agree to the terms of both the <a href="https://github.com/MLH/mlh-policies/blob/main/contest-terms.md">MLH Contest Terms and Conditions</a> and the <a href="https://github.com/MLH/mlh-policies/blob/main/privacy-policy.md">MLH Privacy Policy</a>.
                      </CheckQuestion>
                      <CheckQuestion name="mlh_email_permission">
                        I authorize MLH to send me occasional emails about relevant events, career opportunities, and community announcements.
                      </CheckQuestion>
                    </Page>
                </MultiPageForm>
            </div>
						*/}
        </>
    )
};

export default ApplicationPage;

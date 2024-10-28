import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';

const ApplicationPage = () => {
  const { user, getAccessTokenSilently } = useAuth0();
  const [status, setStatus] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    school: '',
    major: '',
    graduationYear: '',
  });

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a PDF file');
      setFile(null);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const submitApplication = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a resume file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = await getAccessTokenSilently();
      const submitData = new FormData();
      submitData.append('resume', file);
      submitData.append('userId', user.sub);
      submitData.append('email', user.email);
      submitData.append('name', user.name);
      
      // Append all form data
      Object.keys(formData).forEach(key => {
        submitData.append(key, formData[key]);
      });

      const response = await axios.post('http://localhost:5000/api/applications/submit', 
        submitData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setStatus(response.data.message);
      setFile(null);
      // Reset form
      setFormData({
        school: '',
        major: '',
        graduationYear: '',
      });
      // Reset file input
      document.getElementById('resume-upload').value = '';
    } catch (error) {
      console.error('Application submission error:', error);
      setError(error.response?.data?.error || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Application Submission</h2>
      
      <form onSubmit={submitApplication}>
        <div>
          <label htmlFor="school">School:</label>
          <input
            type="text"
            id="school"
            name="school"
            value={formData.school}
            onChange={handleInputChange}
            required
          />
        </div>

        <div>
          <label htmlFor="major">Major:</label>
          <input
            type="text"
            id="major"
            name="major"
            value={formData.major}
            onChange={handleInputChange}
            required
          />
        </div>

        <div>
          <label htmlFor="graduationYear">Graduation Year:</label>
          <input
            type="number"
            id="graduationYear"
            name="graduationYear"
            value={formData.graduationYear}
            onChange={handleInputChange}
            required
          />
        </div>

        <div>
          <label htmlFor="resume-upload">
            Upload Resume (PDF only)
          </label>
          <input
            id="resume-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            required
          />
        </div>

        {error && <div style={{color: 'red'}}>{error}</div>}
        {status && <div style={{color: 'green'}}>{status}</div>}

        <button
          type="submit"
          disabled={loading || !file}
        >
          {loading ? 'Submitting...' : 'Submit Application'}
        </button>
      </form>
    </div>
  );
};

export default ApplicationPage;
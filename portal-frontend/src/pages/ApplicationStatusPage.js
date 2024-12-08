import React, { useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import WhiteBackground from '../components/WhiteBackground';

// List of items with corresponding info
const statusItems = [
  { label: "Name", value: "armando bacot" },
  { label: "Email", value: "test@mrbeast.edu" },
  { label: "School", value: "Washington State University" },
  { label: "Major", value: "carpet consumption" },
  { label: "Grad. Year", value: "1776 B.C." },
  { label: "Something", value: "something" },
  { label: "Something", value: "something" },
  { label: "Something", value: "something" },
  { label: "Something", value: "something" },
];

const StatusList = () => {
  return (
    <div
      style={{
        position: 'absolute',
        top: '20vh',
        left: '0',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        zIndex: '10',
      }}
    >
      <div
        style={{
          width: '80%',
          display: 'grid',
          gridTemplateColumns: 'auto 1fr', // Two columns: labels and values
          rowGap: '1rem', // Space between rows
          columnGap: '2rem', // Space between label and value
        }}
      >
        {statusItems.map((item, index) => (
          <React.Fragment key={index}>
            <div
              style={{
                fontWeight: 'bold',
                color: '#0047ab',
                textAlign: 'right', // Align labels to the right
              }}
            >
              {item.label}
            </div>
            <div
              style={{
                color: '#0047ab',
                textAlign: 'left', // Align values to the left
              }}
            >
              {item.value}
            </div>
          </React.Fragment>
        ))}
      </div>
      
    </div>
  );
};

const ApplicationStatusPage = () => {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
  }, []);

  return (
    <div style={{ position: 'relative', height: '100vh' }}>
        <Navbar />
        <WhiteBackground />
        <div
            className="login-heading"
            style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '20vh',
            margin: '0',
            fontSize: '2rem',
            textAlign: 'center',
            }}
        >
            Applicant Status
        </div>
        
        <div 
            style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                marginLeft: '20%'
            }}
          >
            <StatusList />
        </div>
      
    </div>
  );
};

export default ApplicationStatusPage;

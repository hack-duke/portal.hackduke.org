import React, { useEffect } from 'react';
import HeroBackground from '../components/HeroBackground';
import { Navbar } from '../components/Navbar';
import './ApplicationStatusPage.css'

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
    <div className="status-list" style={{ zIndex: 100, position: 'relative' }}>
      <div className="status-items">
        {statusItems.map((item, index) => (
          <div className="status-item" key={index}>
            <div className="status-label">{item.label}</div>
            <div className="status-value">{item.value}</div>
          </div>
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
    <>
      
      <HeroBackground />
      <Navbar />
      <h1 className='status-title'>Applicant Status</h1>
      <StatusList />
    </>
  );
};

export default ApplicationStatusPage;

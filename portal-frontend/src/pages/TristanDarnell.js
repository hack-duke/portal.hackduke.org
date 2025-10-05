import "./TristanDarnell.css";

const AboutMe = () => {
  return (
    <div className="about-me-container">
      <div className="about-header">
        <h1 className="name-title">Tristan Darnell</h1>
        <p className="location">Orlando, Florida</p>
      </div>

      <div className="about-content">
        <div className="bio-section">
          <h2>About Me</h2>
          <p className="bio-text">
            My name is Tristan Darnell, and I have lived in Orlando, Florida my
            entire life. I have gone to the same school from K-12th grade and so
            my friends and I have all gotten really close. I also started my own
            business during Covid, which was pretty successful and I continued
            that until I go to Duke. Some of the things I enjoy doing are:
            Thrifting, rock climbing, urban exploring and going to the gym.
          </p>
        </div>

        <div className="photos-section">
          <h3>Me and friends</h3>
          <div className="photos-grid">
            <img
              src="/images/Tristan1.JPG"
              alt="Tristan1"
              className="profile-photo"
            />
            <img
              src="/images/Tristan2.JPG"
              alt="Tristan2"
              className="profile-photo"
            />
            <img
              src="/images/Tristan3.JPG"
              alt="Tristan3"
              className="profile-photo"
            />
            <img
              src="/images/Tristan4.JPG"
              alt="Tristan4"
              className="profile-photo"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutMe;

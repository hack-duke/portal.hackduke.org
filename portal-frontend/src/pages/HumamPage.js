import "./HumamPage.css"; // Import your CSS

const MyPage = () => {
  return (
    <div className="about-me-container">
      {/* Header Section */}
      <div className="about-header">
        <h1 className="name-title">Humam Al-Shami</h1>
        <p className="location">Magnolia, Arkansas</p>
      </div>

      {/* Main Content */}
      <div className="about-content">
        {/* Bio Section */}
        <div className="bio-section">
          <h2>About Me</h2>
          <p className="bio-text">
            Hey! I'm Humam, a freshman at Duke studying CS & Stats. I'm
            interested in Machine Learning, Software Engineering, and
            Cybersecurity.
          </p>

          {/* Optional: Hobbies List */}
          <div className="hobbies-list">
            <h2>Hobbies:</h2>
            <span>Swimming</span>
            <span> Video Games</span>
            <span> Anime</span>
          </div>
        </div>

        {/* Photos Section */}
        <div className="photos-section">
          <h3>My Photos</h3>
          <div className="photos-grid">
            <img
              src="/images/HumamImage3.jpg"
              alt="Photo1"
              className="profile-photo"
            />
            <img
              src="/images/HumamImage2.jpeg"
              alt="Photo2"
              className="profile-photo"
            />
            <img
              src="/images/HumamImage1.jpg"
              alt="Photo3"
              className="profile-photo"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyPage;

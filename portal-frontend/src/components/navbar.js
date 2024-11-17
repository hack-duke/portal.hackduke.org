import './navbar.css';

export const Navbar = () => {
    return (
      <nav class = 'navbar' style={{
        backgroundImage: `url(/images/Rectangle_360.png)`
      }}>
        <button 
            className="Logo" 
            style={{
                backgroundImage: `url(/images/Small_Logo.png)`,
                backgroundSize: 'cover',       
                backgroundPosition: 'center',    
                backgroundColor: 'transparent',
                width: '68px',            
                height: '68px',                  
                border: 'none',               
                cursor: 'pointer',              
                color: 'transparent',            
                textIndent: '-9999px',  
                marginLeft: '60px',     
                marginRight: '0',   
            }}
            onClick={() => window.open("https://hackduke.org", "_blank")}>
            HackDuke
        </button>

        {/* <button 
            className="Logo" 
            style={{
                backgroundImage: `url(/images/HackDuke.png)`,
                backgroundSize: 'cover',       
                backgroundPosition: 'center',    
                backgroundColor: 'transparent',
                width: '285px',            
                height: '37.71px',                  
                border: 'none',               
                cursor: 'pointer',              
                color: 'transparent',            
                textIndent: '-9999px',
                marginRight: '5%',         
            }}
            onClick={() => window.open("https://hackduke.org", "_blank")}>
            HackDuke
        </button> */}
      </nav>
    )
}

export default Navbar

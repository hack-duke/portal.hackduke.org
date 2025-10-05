import { useState, useEffect } from "react";
import "./ReactOverview.css";

// Small reusable components for examples
function WelcomeMessage() {
  return (
    <div className="example-component welcome">
      <h3>Welcome to Our Portal</h3>
      <p>Get started by exploring our features.</p>
    </div>
  );
}

function ProfileCard({ name, role }) {
  return (
    <div className="profile-card">
      <h3>{name}</h3>
      <p className="role">{role}</p>
      <button onClick={() => alert(`Hello ${name}!`)}>Say Hello</button>
    </div>
  );
}

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div className="counter">
      <p className="count-display">Count: {count}</p>
      <div className="counter-buttons">
        <button onClick={() => setCount(count + 1)}>Increment</button>
        <button onClick={() => setCount(0)}>Reset</button>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description, ctaText = "Learn More" }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="feature-card">
      <div className="icon-wrapper">
        <span className="icon">{icon}</span>
      </div>

      <h3 className="feature-title">{title}</h3>

      <p className={`feature-description ${isExpanded ? "expanded" : ""}`}>
        {description}
      </p>

      {description.length > 100 && (
        <button
          className="expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? "Show Less" : "Read More"}
        </button>
      )}

      <button className="cta-button">{ctaText}</button>
    </div>
  );
}

function WindowSize() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <p className="window-size">Window width: {width}px</p>;
}

function ResponsiveNav() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="demo-navbar">
      <div className="nav-brand">Logo</div>

      <button className="menu-toggle" onClick={() => setIsOpen(!isOpen)}>
        ☰
      </button>

      <ul className={`nav-links ${isOpen ? "open" : ""}`}>
        <li>
          <a href="#home">Home</a>
        </li>
        <li>
          <a href="#about">About</a>
        </li>
        <li>
          <a href="#contact">Contact</a>
        </li>
      </ul>
    </nav>
  );
}

function ReactOverview() {
  return (
    <div className="react-overview">
      <header className="overview-header">
        <h1>React Frontend Development: Complete Overview</h1>
        <p className="subtitle">
          A comprehensive guide to building modern web applications with React
        </p>
      </header>

      <div className="content-container">
        {/* Section 1: What is React? */}
        <section className="lesson-section" id="section-1">
          <div className="section-header">
            <span className="section-number">1</span>
            <h2>What is React?</h2>
          </div>
          <div className="section-content">
            <p>
              <strong>React</strong> is a JavaScript library for building user
              interfaces, created and maintained by Meta (Facebook). It allows
              you to build complex, interactive web applications by breaking
              them down into reusable, independent pieces called{" "}
              <strong>components</strong>.
            </p>

            <div className="key-concepts">
              <h3>Key Concepts:</h3>
              <ul>
                <li>
                  <strong>Component-Based:</strong> Build encapsulated
                  components that manage their own state
                </li>
                <li>
                  <strong>Declarative:</strong> Describe what you want to see,
                  React handles the how
                </li>
                <li>
                  <strong>Learn Once, Write Anywhere:</strong> Use the same
                  concepts across web, mobile (React Native), and more
                </li>
              </ul>
            </div>

            <div className="why-react">
              <h3>Why React?</h3>
              <ul>
                <li>
                  <strong>Reusability:</strong> Write a component once, use it
                  everywhere
                </li>
                <li>
                  <strong>Efficiency:</strong> React only updates what needs to
                  change (Virtual DOM)
                </li>
                <li>
                  <strong>Large Ecosystem:</strong> Tons of libraries, tools,
                  and community support
                </li>
                <li>
                  <strong>Industry Standard:</strong> Used by Facebook, Netflix,
                  Airbnb, and thousands of companies
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Section 2: Core Frontend Concepts */}
        <section className="lesson-section" id="section-2">
          <div className="section-header">
            <span className="section-number">2</span>
            <h2>Core Frontend Concepts</h2>
          </div>

          {/* 2.1 Components */}
          <div className="subsection">
            <h3>2.1 Components</h3>
            <p>
              Components are the building blocks of React applications. Think of
              them as custom, reusable HTML elements.
            </p>

            <div className="example-box">
              <h4>Example: A Simple Component</h4>
              <pre className="code-block">{`function WelcomeMessage() {
  return (
    <div className="welcome">
      <h3>Welcome to Our Portal</h3>
      <p>Get started by exploring our features.</p>
    </div>
  );
}`}</pre>
              <div className="live-example">
                <h4>Live Example:</h4>
                <WelcomeMessage />
              </div>
            </div>

            <div className="best-practices">
              <h4>Component Best Practices:</h4>
              <ul>
                <li>One component per file</li>
                <li>
                  Keep components small and focused (single responsibility)
                </li>
                <li>
                  Name components clearly (e.g., <code>UserProfile</code>,{" "}
                  <code>NavigationBar</code>)
                </li>
                <li>Use PascalCase for component names</li>
              </ul>
            </div>
          </div>

          {/* 2.2 JSX */}
          <div className="subsection">
            <h3>2.2 JSX (JavaScript XML)</h3>
            <p>
              JSX lets you write HTML-like code in JavaScript. It makes
              components readable and intuitive.
            </p>

            <div className="example-box">
              <h4>Example: Using JSX with Props</h4>
              <pre className="code-block">{`function ProfileCard({ name, role }) {
  return (
    <div className="profile-card">
      <h3>{name}</h3>
      <p className="role">{role}</p>
      <button onClick={() => alert(\`Hello \${name}!\`)}>
        Say Hello
      </button>
    </div>
  );
}`}</pre>
              <div className="live-example">
                <h4>Live Example:</h4>
                <div className="profile-grid">
                  <ProfileCard name="Alex Chen" role="Developer" />
                  <ProfileCard name="Jordan Smith" role="Designer" />
                </div>
              </div>
            </div>

            <div className="jsx-rules">
              <h4>JSX Rules:</h4>
              <ul>
                <li>
                  Use <code>className</code> instead of <code>class</code>
                </li>
                <li>
                  Close all tags (even <code>&lt;img /&gt;</code>,{" "}
                  <code>&lt;br /&gt;</code>)
                </li>
                <li>
                  Use camelCase for attributes (<code>onClick</code>, not{" "}
                  <code>onclick</code>)
                </li>
                <li>
                  Wrap multiple elements in a parent (or use fragments{" "}
                  <code>&lt;&gt;...&lt;/&gt;</code>)
                </li>
              </ul>
            </div>
          </div>

          {/* 2.3 Props */}
          <div className="subsection">
            <h3>2.3 Props (Properties)</h3>
            <p>
              Props pass data from parent components to child components.
              They're like function parameters.
            </p>

            <div className="best-practices">
              <h4>Props Best Practices:</h4>
              <ul>
                <li>
                  Props are <strong>read-only</strong> (never modify them)
                </li>
                <li>Use destructuring for cleaner code</li>
                <li>Provide default values when needed</li>
                <li>Use PropTypes or TypeScript for type checking</li>
              </ul>
            </div>
          </div>

          {/* 2.4 State */}
          <div className="subsection">
            <h3>2.4 State</h3>
            <p>
              State is data that changes over time within a component. Use the{" "}
              <code>useState</code> hook to manage it.
            </p>

            <div className="example-box">
              <h4>Example: Interactive Counter with State</h4>
              <pre className="code-block">{`function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div className="counter">
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
      <button onClick={() => setCount(0)}>
        Reset
      </button>
    </div>
  );
}`}</pre>
              <div className="live-example">
                <h4>Live Example:</h4>
                <Counter />
              </div>
            </div>

            <div className="best-practices">
              <h4>State Best Practices:</h4>
              <ul>
                <li>Keep state as local as possible</li>
                <li>Don't mutate state directly (use setter functions)</li>
                <li>Lift state up to share between components</li>
                <li>
                  Consider using context or state management for complex apps
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Section 3: Responsive Design */}
        <section className="lesson-section" id="section-3">
          <div className="section-header">
            <span className="section-number">3</span>
            <h2>Responsive Design in React</h2>
          </div>

          <div className="subsection">
            <h3>3.1 Mobile-First Approach</h3>
            <p>
              Design for mobile screens first, then enhance for larger screens.
            </p>

            <div className="why-box">
              <h4>Why Mobile-First?</h4>
              <ul>
                <li>Most users browse on mobile devices</li>
                <li>
                  Easier to expand simple designs than simplify complex ones
                </li>
                <li>Forces you to prioritize essential content</li>
              </ul>
            </div>
          </div>

          <div className="subsection">
            <h3>3.2 Responsive Layout Examples</h3>
            <p>Compare bad and good responsive design approaches:</p>

            <div className="comparison-container">
              <div className="comparison-item">
                <h4>❌ Bad: Fixed Width</h4>
                <p className="comparison-note">
                  Scroll horizontally to see the overflow →
                </p>
                <div className="bad-responsive-example">
                  <div className="bad-card">Card 1 - Too wide!</div>
                  <div className="bad-card">Card 2 - Too wide!</div>
                  <div className="bad-card">Card 3 - Too wide!</div>
                </div>
                <pre className="code-block small">{`.bad-card {
  width: 200px; /* Fixed width */
  min-width: 200px;
  /* Forces overflow! */
}`}</pre>
              </div>

              <div className="comparison-item">
                <h4>✅ Good: Flexible Width</h4>
                <p className="comparison-note">
                  Cards adapt to available space
                </p>
                <div className="good-responsive-example">
                  <div className="good-card">Card 1 - Flexible!</div>
                  <div className="good-card">Card 2 - Flexible!</div>
                  <div className="good-card">Card 3 - Flexible!</div>
                </div>
                <pre className="code-block small">{`.good-card {
  max-width: 100%;
  flex: 1;
  /* Adapts to container */
}`}</pre>
              </div>
            </div>

            <div className="comparison-container">
              <div className="comparison-item">
                <h4>❌ Bad: No Media Queries</h4>
                <p className="comparison-note">
                  Always 4 columns - too cramped on mobile!
                </p>
                <div className="bad-grid">
                  <div className="grid-item">1</div>
                  <div className="grid-item">2</div>
                  <div className="grid-item">3</div>
                  <div className="grid-item">4</div>
                </div>
                <pre className="code-block small">{`.bad-grid {
  display: grid;
  grid-template-columns:
    repeat(4, 1fr);
  /* Always 4 columns! */
}`}</pre>
              </div>

              <div className="comparison-item">
                <h4>✅ Good: Responsive Grid</h4>
                <p className="comparison-note">
                  Adapts: 1 col → 2 cols → 4 cols
                </p>
                <div className="good-grid">
                  <div className="grid-item">1</div>
                  <div className="grid-item">2</div>
                  <div className="grid-item">3</div>
                  <div className="grid-item">4</div>
                </div>
                <pre className="code-block small">{`.good-grid {
  grid-template-columns: 1fr;
}
@media (min-width: 640px) {
  grid-template-columns:
    repeat(2, 1fr);
}
@media (min-width: 1024px) {
  grid-template-columns:
    repeat(4, 1fr);
}`}</pre>
              </div>
            </div>
          </div>

          <div className="subsection">
            <h3>3.3 Responsive Navigation</h3>
            <p>
              A navigation that adapts from mobile hamburger menu to desktop
              horizontal menu:
            </p>
            <div className="example-box">
              <div className="live-example">
                <ResponsiveNav />
              </div>
              <pre className="code-block">{`function ResponsiveNav() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="nav-brand">Logo</div>

      <button
        className="menu-toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        ☰
      </button>

      <ul className={\`nav-links \${isOpen ? 'open' : ''}\`}>
        <li><a href="#home">Home</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
  );
}`}</pre>
            </div>
          </div>

          <div className="subsection">
            <h3>3.4 Viewport-Based Sizing</h3>
            <p>
              Use viewport units and modern CSS functions for truly responsive
              sizing:
            </p>
            <div className="example-box">
              <pre className="code-block">{`.hero-title {
  /* Scales with viewport,
     min 2rem, max 4rem */
  font-size: clamp(2rem, 5vw, 4rem);
}

.container {
  /* 90% width, but never
     more than 1200px */
  width: min(90%, 1200px);
  margin: 0 auto;
}`}</pre>
            </div>
          </div>
        </section>

        {/* Section 4: Design Best Practices */}
        <section className="lesson-section" id="section-4">
          <div className="section-header">
            <span className="section-number">4</span>
            <h2>Design Best Practices</h2>
          </div>

          <div className="subsection">
            <h3>4.1 Consistent Spacing</h3>
            <p>Use a spacing scale (e.g., 4px base unit) for consistency:</p>
            <div className="spacing-demo">
              <div className="space-xs">xs: 4px</div>
              <div className="space-sm">sm: 8px</div>
              <div className="space-md">md: 16px</div>
              <div className="space-lg">lg: 24px</div>
              <div className="space-xl">xl: 32px</div>
            </div>
            <pre className="code-block">{`:root {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
}`}</pre>
          </div>

          <div className="subsection">
            <h3>4.2 Typography Hierarchy</h3>
            <div className="typography-demo">
              <h1 className="text-4xl">4XL Heading (36px)</h1>
              <h2 className="text-3xl">3XL Heading (30px)</h2>
              <h3 className="text-2xl">2XL Heading (24px)</h3>
              <h4 className="text-xl">XL Heading (20px)</h4>
              <p className="text-base">Base Text (16px)</p>
              <p className="text-sm">Small Text (14px)</p>
            </div>
            <pre className="code-block">{`:root {
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  --font-size-4xl: 2.25rem;  /* 36px */
}`}</pre>
          </div>

          <div className="subsection">
            <h3>4.3 Color System</h3>
            <p>Define a consistent color palette:</p>
            <div className="color-demo">
              <div className="color-box primary">Primary</div>
              <div className="color-box success">Success</div>
              <div className="color-box warning">Warning</div>
              <div className="color-box error">Error</div>
              <div className="color-box gray">Gray</div>
            </div>
            <pre className="code-block">{`:root {
  --primary: #3b82f6;
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --gray: #6b7280;
}`}</pre>
          </div>

          <div className="subsection">
            <h3>4.4 Accessible Design</h3>
            <div className="accessibility-demo">
              <button className="accessible-btn">Accessible Button</button>
              <p className="accessibility-note">
                ✓ Min height 44px for touch
                <br />
                ✓ Clear focus outline
                <br />
                ✓ Good color contrast
                <br />✓ Hover feedback
              </p>
            </div>
            <pre className="code-block">{`.accessible-btn {
  min-height: 44px;
  padding: 12px 24px;
  font-size: 16px;
}

.accessible-btn:focus {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.accessible-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}`}</pre>
          </div>
        </section>

        {/* Section 5: Practical Example */}
        <section className="lesson-section" id="section-5">
          <div className="section-header">
            <span className="section-number">5</span>
            <h2>Practical Example: Feature Cards</h2>
          </div>

          <div className="subsection">
            <p>
              Here's a responsive feature card component that combines all the
              concepts we've learned:
            </p>

            <div className="feature-cards-grid">
              <FeatureCard
                icon="🚀"
                title="Fast Performance"
                description="Built with React's virtual DOM for lightning-fast updates and optimal performance across all devices."
                ctaText="Learn More"
              />
              <FeatureCard
                icon="🎨"
                title="Beautiful Design"
                description="Carefully crafted components with attention to detail, accessibility, and user experience that delights users."
                ctaText="Explore"
              />
              <FeatureCard
                icon="📱"
                title="Fully Responsive"
                description="Works seamlessly on mobile, tablet, and desktop with a mobile-first approach to design."
                ctaText="Try It"
              />
            </div>

            <pre className="code-block">{`function FeatureCard({ icon, title, description, ctaText }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="feature-card">
      <div className="icon-wrapper">
        <span className="icon">{icon}</span>
      </div>
      <h3>{title}</h3>
      <p className={\`description \${isExpanded ? 'expanded' : ''}\`}>
        {description}
      </p>
      {description.length > 100 && (
        <button onClick={() => setIsExpanded(!isExpanded)}>
          {isExpanded ? 'Show Less' : 'Read More'}
        </button>
      )}
      <button className="cta-button">{ctaText}</button>
    </div>
  );
}`}</pre>
          </div>
        </section>

        {/* Section 6: Common Patterns */}
        <section className="lesson-section" id="section-6">
          <div className="section-header">
            <span className="section-number">6</span>
            <h2>Common Patterns & Tips</h2>
          </div>

          <div className="subsection">
            <h3>6.1 Conditional Rendering</h3>
            <pre className="code-block">{`function UserGreeting({ user }) {
  return (
    <div>
      {user ? (
        <h1>Welcome back, {user.name}!</h1>
      ) : (
        <h1>Please sign in</h1>
      )}
    </div>
  );
}`}</pre>
          </div>

          <div className="subsection">
            <h3>6.2 Lists & Keys</h3>
            <pre className="code-block">{`function TodoList({ todos }) {
  return (
    <ul className="todo-list">
      {todos.map(todo => (
        <li key={todo.id}>
          {todo.text}
        </li>
      ))}
    </ul>
  );
}

// Always use unique, stable keys
// (IDs, not array indices)`}</pre>
          </div>

          <div className="subsection">
            <h3>6.3 Event Handling</h3>
            <pre className="code-block">{`function SearchBar() {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Searching for:', query);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
      />
      <button type="submit">Search</button>
    </form>
  );
}`}</pre>
          </div>

          <div className="subsection">
            <h3>6.4 useEffect for Side Effects</h3>
            <div className="example-box">
              <pre className="code-block">{`function WindowSize() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);

    // Cleanup function
    return () => window.removeEventListener('resize', handleResize);
  }, []); // Empty array = run once on mount

  return <p>Window width: {width}px</p>;
}`}</pre>
              <div className="live-example">
                <h4>Live Example (resize your window):</h4>
                <WindowSize />
              </div>
            </div>
          </div>
        </section>

        {/* Section 7: Key Takeaways */}
        <section className="lesson-section" id="section-7">
          <div className="section-header">
            <span className="section-number">7</span>
            <h2>Key Takeaways</h2>
          </div>

          <div className="takeaways-grid">
            <div className="takeaway-card">
              <h3>&#x1F9E9; Think in Components</h3>
              <p>Break your UI into small, reusable pieces</p>
            </div>
            <div className="takeaway-card">
              <h3>&#x1F4F1; Mobile-First</h3>
              <p>Design for small screens first, enhance for larger screens</p>
            </div>
            <div className="takeaway-card">
              <h3>&#x1F3AF; Use Modern CSS</h3>
              <p>Flexbox and Grid make responsive design much easier</p>
            </div>
            <div className="takeaway-card">
              <h3>&#x1F3A8; Design System</h3>
              <p>
                Use spacing scales, color palettes, and typography hierarchies
              </p>
            </div>
            <div className="takeaway-card">
              <h3>&#x267F; Accessibility</h3>
              <p>
                Consider keyboard navigation, screen readers, and touch targets
              </p>
            </div>
            <div className="takeaway-card">
              <h3>&#x1F4A1; Keep It Simple</h3>
              <p>Start simple, add complexity only when needed</p>
            </div>
          </div>
        </section>

        {/* Section 8: Next Steps */}
        <section className="lesson-section" id="section-8">
          <div className="section-header">
            <span className="section-number">8</span>
            <h2>Next Steps</h2>
          </div>

          <div className="next-steps">
            <ul>
              <li>Build a simple portfolio page with responsive cards</li>
              <li>Create a navigation component that adapts to mobile</li>
              <li>
                Experiment with different layout patterns (sidebar, grid,
                masonry)
              </li>
              <li>Try implementing a dark mode toggle</li>
              <li>Practice with Tailwind CSS for faster development</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}

export default ReactOverview;

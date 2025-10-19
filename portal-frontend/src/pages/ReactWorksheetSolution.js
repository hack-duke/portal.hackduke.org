import { useState } from "react";
import "./ReactWorksheetSolution.css";

/*
  ============================================================================
  REACT WORKSHEET - SOLUTION KEY
  ============================================================================

  This file contains the solutions to all exercises in the React Worksheet.

  Exercises covered:
  - JSX syntax (Exercise 1)
  - Props (Exercises 2, 4)
  - State with useState (Exercises 3, 5, 6, 7)
  - Event handling (Exercises 3, 5, 6, 7)
  - List rendering (Exercises 9, 10)
  - Responsive design (Exercises 7, 8, 9)
*/

// ==================== EXERCISE 1: Fix JSX Syntax - SOLUTION ====================
// ✅ Fixed all 4 JSX syntax errors:
// 1. Changed class to className
// 2. Closed the h2 tag properly
// 3. Changed onclick to onClick (camelCase)
// 4. Self-closed the img tag with />
function WelcomeCard() {
  return (
    <div className="welcome-card">
      <h2>Welcome to React!</h2>
      <p>This is your first exercise.</p>
      <button onClick={() => alert('Hello')}>Click Me</button>
      <img src="https://via.placeholder.com/150" alt="Placeholder" />
    </div>
  );
}

// ==================== EXERCISE 2: Add Props - SOLUTION ====================
// ✅ Added props destructuring and used them in the component
function BookCard({ title, author }) {
  return (
    <div className="book-card">
      <h3>{title}</h3>
      <p className="author">{author}</p>
      <button>Read More</button>
    </div>
  );
}

// ==================== EXERCISE 3: Fix State Management - SOLUTION ====================
// ✅ Fixed the decrement button to actually decrement
// ✅ Added onClick handler to reset button
// ✅ Prevented count from going below 0 using Math.max
function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div className="counter-exercise">
      <h3>Counter: {count}</h3>
      <div className="counter-buttons">
        <button onClick={() => setCount(count + 1)}>+</button>
        <button onClick={() => setCount(Math.max(0, count - 1))}>-</button>
        <button onClick={() => setCount(0)}>Reset</button>
      </div>
    </div>
  );
}

// ==================== EXERCISE 4: Create a Component with Props - SOLUTION ====================
// ✅ Created ProductCard component with all required props
// ✅ Displayed image, name, formatted price
// ✅ Conditional button text based on inStock
// ✅ Disabled button when out of stock
function ProductCard({ name, price, inStock, image }) {
  return (
    <div className="product-card">
      <img src={image} alt={name} />
      <h3>{name}</h3>
      <p className="price">${price.toFixed(2)}</p>
      <button disabled={!inStock}>
        {inStock ? "Add to Cart" : "Out of Stock"}
      </button>
    </div>
  );
}

// ==================== EXERCISE 5: Interactive Toggle - SOLUTION ====================
// ✅ Added useState to track visibility
// ✅ Created toggle button with conditional text
// ✅ Conditionally rendered content based on state
function ToggleContent() {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="toggle-exercise">
      <h3>Product Information</h3>
      <button onClick={() => setIsVisible(!isVisible)}>
        {isVisible ? "Hide Details" : "Show Details"}
      </button>
      {isVisible && (
        <div className="toggle-content">
          <p>
            This is a premium product with excellent features and quality
            craftsmanship. It comes with a 1-year warranty and free shipping.
          </p>
        </div>
      )}
    </div>
  );
}

// ==================== EXERCISE 6: Form with Controlled Input - SOLUTION ====================
// ✅ Added state for name
// ✅ Made input controlled with value and onChange
// ✅ Created handleSubmit to prevent default and clear input
// ✅ Displayed greeting when name is entered
function GreetingForm() {
  const [name, setName] = useState("");
  const [submittedName, setSubmittedName] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmittedName(name);
    setName("");
  };

  return (
    <div className="form-exercise">
      <h3>Enter Your Name</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Your name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button type="submit">Submit</button>
      </form>
      {submittedName && (
        <div className="greeting-display">
          Hello, {submittedName}! 👋
        </div>
      )}
    </div>
  );
}

// ==================== EXERCISE 7: Fix Responsive Navbar - SOLUTION ====================
// ✅ Added state to track menu open/close
// ✅ Created hamburger button with onClick handler
// ✅ Conditionally applied 'open' class to nav-links
// ✅ CSS handles responsive behavior (see CSS file)
function ResponsiveNavbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="worksheet-navbar">
      <div className="nav-brand">MyApp</div>

      <button className="menu-toggle" onClick={() => setIsOpen(!isOpen)}>
        ☰
      </button>

      <ul className={`nav-links ${isOpen ? "open" : ""}`}>
        <li><a href="#home">Home</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#services">Services</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
  );
}

// ==================== EXERCISE 8: Fix Responsive Button - SOLUTION ====================
// ✅ Solution is in the CSS file (see .responsive-btn styles)
function ResponsiveButton() {
  return (
    <div className="button-exercise">
      <h3>Responsive Button Exercise</h3>
      <button className="responsive-btn">Click Me!</button>
      <p className="hint">
        ✅ Button now has proper touch target size and responsive styling!
      </p>
    </div>
  );
}

// ==================== EXERCISE 9: Create Card Grid - SOLUTION ====================
// ✅ Used .map() to render cards with unique keys
// ✅ Displayed title and text for each card
// ✅ CSS handles responsive grid (see CSS file)
function CardGrid() {
  const cards = [
    { id: 1, title: "Card 1", text: "First card" },
    { id: 2, title: "Card 2", text: "Second card" },
    { id: 3, title: "Card 3", text: "Third card" },
    { id: 4, title: "Card 4", text: "Fourth card" },
    { id: 5, title: "Card 5", text: "Fifth card" },
    { id: 6, title: "Card 6", text: "Sixth card" },
  ];

  return (
    <div className="grid-exercise">
      <h3>Responsive Grid Exercise</h3>
      <div className="card-grid">
        {cards.map((card) => (
          <div key={card.id} className="card-grid-item">
            <h4>{card.title}</h4>
            <p>{card.text}</p>
          </div>
        ))}
      </div>
      <p className="hint">
        ✅ Grid now responds to screen size: 1 col → 2 cols → 3 cols!
      </p>
    </div>
  );
}

// ==================== EXERCISE 10: List Rendering with Keys - SOLUTION ====================
// ✅ Used .map() to render todos with unique keys
// ✅ Added checkbox for each todo
// ✅ Applied 'completed' class conditionally
function TodoList() {
  const todos = [
    { id: 1, text: "Learn React components", completed: false },
    { id: 2, text: "Understand JSX", completed: true },
    { id: 3, text: "Master useState", completed: false },
    { id: 4, text: "Build responsive layouts", completed: false },
  ];

  return (
    <div className="todo-exercise">
      <h3>Todo List</h3>
      <ul className="todo-list">
        {todos.map((todo) => (
          <li key={todo.id} className={todo.completed ? "completed" : ""}>
            <input
              type="checkbox"
              defaultChecked={todo.completed}
              id={`todo-${todo.id}`}
            />
            <label htmlFor={`todo-${todo.id}`}>{todo.text}</label>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ==================== Main Worksheet Component ====================
function ReactWorksheetSolution() {
  return (
    <div className="react-worksheet">
      <header className="worksheet-header">
        <h1>React Workshop Worksheet - SOLUTIONS</h1>
        <p className="subtitle">
          ✅ All exercises completed correctly!
        </p>
        <p className="subtitle">
          Use this as a reference to check your work.
        </p>
      </header>

      <div className="exercises-container">
        {/* Exercise 1 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">1</span>
            <h2>Fix JSX Syntax ✅</h2>
          </div>
          <p className="exercise-description">
            Fixed: className, closed h2 tag, onClick (camelCase), self-closed img tag
          </p>
          <WelcomeCard />
        </section>

        {/* Exercise 2 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">2</span>
            <h2>Use Props ✅</h2>
          </div>
          <p className="exercise-description">
            BookCard now accepts and displays title and author props
          </p>
          <div className="book-grid">
            <BookCard title="To Kill a Mockingbird" author="Harper Lee" />
            <BookCard title="1984" author="George Orwell" />
            <BookCard title="The Great Gatsby" author="F. Scott Fitzgerald" />
          </div>
        </section>

        {/* Exercise 3 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">3</span>
            <h2>Fix State Management ✅</h2>
          </div>
          <p className="exercise-description">
            Fixed decrement button, reset button, and prevented negative counts
          </p>
          <Counter />
        </section>

        {/* Exercise 4 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">4</span>
            <h2>Create Component with Props ✅</h2>
          </div>
          <p className="exercise-description">
            Created ProductCard with image, name, price, and conditional button
          </p>
          <div className="product-grid">
            <ProductCard
              name="Wireless Headphones"
              price={79.99}
              inStock={true}
              image="https://via.placeholder.com/200x150?text=Headphones"
            />
            <ProductCard
              name="Smart Watch"
              price={199.99}
              inStock={false}
              image="https://via.placeholder.com/200x150?text=Watch"
            />
            <ProductCard
              name="Laptop Stand"
              price={34.99}
              inStock={true}
              image="https://via.placeholder.com/200x150?text=Stand"
            />
          </div>
        </section>

        {/* Exercise 5 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">5</span>
            <h2>Interactive Toggle ✅</h2>
          </div>
          <p className="exercise-description">
            Added state, toggle button, and conditional rendering
          </p>
          <ToggleContent />
        </section>

        {/* Exercise 6 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">6</span>
            <h2>Controlled Form ✅</h2>
          </div>
          <p className="exercise-description">
            Created controlled input with state, onChange, and onSubmit handlers
          </p>
          <GreetingForm />
        </section>

        {/* Exercise 7 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">7</span>
            <h2>Responsive Navbar ✅</h2>
          </div>
          <p className="exercise-description">
            Added hamburger menu with state management and responsive CSS (resize window to test!)
          </p>
          <ResponsiveNavbar />
        </section>

        {/* Exercise 8 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">8</span>
            <h2>Responsive Button (CSS) ✅</h2>
          </div>
          <p className="exercise-description">
            Fixed CSS with proper touch targets, padding, and hover effects
          </p>
          <ResponsiveButton />
        </section>

        {/* Exercise 9 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">9</span>
            <h2>Responsive Grid (CSS) ✅</h2>
          </div>
          <p className="exercise-description">
            Used .map() for rendering and added responsive grid CSS (resize to see columns change!)
          </p>
          <CardGrid />
        </section>

        {/* Exercise 10 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">10</span>
            <h2>List Rendering ✅</h2>
          </div>
          <p className="exercise-description">
            Used .map() with unique keys, checkboxes, and conditional className
          </p>
          <TodoList />
        </section>
      </div>

      <footer className="worksheet-footer">
        <h2>All Exercises Complete! 🎉</h2>
        <p>Great job completing all the React exercises!</p>
        <ul>
          <li>Mastered JSX syntax rules</li>
          <li>Learned to use props effectively</li>
          <li>Practiced state management with useState</li>
          <li>Implemented event handling</li>
          <li>Created responsive designs</li>
          <li>Used .map() for list rendering</li>
        </ul>
      </footer>
    </div>
  );
}

export default ReactWorksheetSolution;

import { useState } from "react";
import "./ReactWorksheet.css";

/*
  ============================================================================
  REACT WORKSHEET - Fix the code below!
  ============================================================================

  IMPORTANT: Start with Exercise 1!

  Exercise 1 has SYNTAX ERRORS that prevent the entire website from rendering.
  You MUST fix all the syntax errors in Exercise 1 before you can see anything
  on the page. Once those are fixed, the website will render and you can see
  all the other exercises.

  This worksheet tests your understanding of:
  - JSX syntax (Exercise 1) ← START HERE!
  - Props (Exercises 2, 4)
  - State with useState (Exercises 3, 5, 6, 7)
  - Event handling (Exercises 3, 5, 6, 7)
  - List rendering (Exercises 9, 10)
  - Responsive design (Exercises 7, 8, 9)

  Look for TODO comments to know what to fix!
*/

// ==================== EXERCISE 1: Fix JSX Syntax ====================
// ⚠️ CRITICAL: This component has JSX SYNTAX ERRORS that prevent rendering!
//
// THE WEBSITE WILL NOT RENDER UNTIL YOU FIX ALL 4 ERRORS BELOW!
//
// TODO: Find and fix these 4 JSX syntax errors:
// 1. Use className instead of class
// 2. Close the h2 tag properly
// 3. Use onClick instead of onclick (camelCase for event handlers)
// 4. Self-close the img tag with />
//
// After fixing all 4 errors, save the file and the website should render!

//UNCOMMENT THIS CODE AND FIX THE 4 ERRORS:

function WelcomeCard() {
  return (
    <div className="welcome-card">
      <h2>Welcome</h2>
      <button onClick={() => alert("Hello!")}>Say hi</button>
      <img src="https://via.placeholder.com/300x180" alt="placeholder" />
    </div>
  );
}

//==================== EXERCISE 2: Add Props ====================
//</h2> TODO: This component should accept 'title' and 'author' props and display them
// Currently it shows hardcoded values - make it use props instead!
function BookCard({ title, author }) {
  return (
    <div className="book-card">
      <h3>{title}</h3>
      <p className="author">{author}</p>
      <button>Read More</button>
    </div>
  );
}

// ==================== EXERCISE 3: Fix State Management ====================
// TODO: This counter has bugs! Fix the state management.
// Hints:
// - The decrement button doesn't work
// - The reset button doesn't work
// - Make sure count never goes below 0
function Counter() {
  const [count, setCount] = useState(0);

  const inc = () => setCount((c) => c + 1);
  const dec = () => setCount((c) => Math.max(0, c - 1));
  const reset = () => setCount(0);

  return (
    <div className="counter-exercise">
      <h3>Counter: {count}</h3>
      <div className="counter-buttons">
        <button onClick={inc} aria_label="Increment">
          +
        </button>
        <button onClick={dec} aria_label="Decrement">
          -
        </button>
        <button onClick={reset} aria-label="Reset">
          Reset
        </button>
      </div>
    </div>
  );
}

// ==================== EXERCISE 4: Create a Component with Props ====================
// TODO: Create a ProductCard component that accepts these props:
// - name (string)
// - price (number)
// - inStock (boolean)
// - image (string - URL)
//
// Display:
// - The product image
// - The product name as an h3
// - The price formatted as "$XX.XX"
// - A button that says "Add to Cart" if inStock is true, or "Out of Stock" if false
// - The button should be disabled when out of stock
//
// Write your component below:

function ProductCard({ name, price, inStock, image }) {
  const formatted = `$${Number(price).toFixed(2)}`;
  return (
    <div className={`product-card ${!inStock ? "out" : ""}`}>
      <img className="product-image" src={image} alt={name} />
      <h3>{name}</h3>
      <p className="price">{formatted}</p>
      <button disabled={!inStock}>
        {inStock ? "Add to Cart" : "Out of Stock"}
      </button>
    </div>
  );
}

// ==================== EXERCISE 5: Interactive Toggle ====================
// TODO: Create a component that toggles between showing and hiding content
// Requirements:
// - Use useState to track if content is visible
// - Show a button that says "Show Details" when hidden, "Hide Details" when shown
// - When visible, show a div with some text content
function ToggleContent() {
  const [open, setOpen] = useState(false);
  return (
    <div className="toggle-exercise">
      <h3>Product Information</h3>
      <button onClick={() => setOpen((o) => !o)}>
        {open ? "Hide Details" : "Show Details"}
      </button>
      {open && (
        <div className="details">
          <p>
            These headphones feature active noise cancellation, 30-hour battery
            life, and quick charge.
          </p>
        </div>
      )}
    </div>
  );
}

// ==================== EXERCISE 6: Form with Controlled Input ====================
// TODO: Make this a controlled form component
// Requirements:
// - Track the input value with useState
// - Update state when input changes
// - Show the entered name below the form
// - Clear the input when form is submitted
function GreetingForm() {
  const [name, setName] = useState("");
  const [submittedName, setSubmittedName] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmittedName(name.trim());
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
      {submittedName && <p className="greeting">Hello, {submittedName}!</p>}
    </div>
  );
}

// ==================== EXERCISE 7: Fix Responsive Navbar ====================
// TODO: This navbar needs to be responsive!
// Requirements:
// - Add a hamburger menu button (use 0 as the icon)
// - The menu button should only show on mobile (< 768px)
// - Track menu open/close state with useState
// - Toggle menu visibility when button is clicked
// - On desktop, links should show horizontally
// - On mobile, links should show vertically when menu is open
function ResponsiveNavbar() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <nav className="worksheet-navbar">
      <div className="nav-brand">MyApp</div>

      <button
        className="menu-toggle"
        aria-label="Toggle menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((v) => !v)}
      >
        0
      </button>

      <ul className={`nav-links ${isOpen ? "open" : ""}`}>
        <li>
          <a href="#home">Home</a>
        </li>
        <li>
          <a href="#about">About</a>
        </li>
        <li>
          <a href="#services">Services</a>
        </li>
        <li>
          <a href="#contact">Contact</a>
        </li>
      </ul>
    </nav>
  );
}

// ==================== EXERCISE 8: Fix Responsive Button ====================
// TODO: Fix the CSS so this button is responsive
// The button should:
// - Have proper touch target size (min 44px height)
// - Scale text appropriately for mobile
// - Have proper padding that works on all screen sizes
// (Fix this in the CSS file!)
function ResponsiveButton() {
  return (
    <div className="button-exercise">
      <h3>Responsive Button Exercise</h3>
      <button className="responsive-btn">Click Me!</button>
      <p className="hint">
        Check the CSS file and fix the .responsive-btn class!
      </p>
    </div>
  );
}

// ==================== EXERCISE 9: Create Card Grid ====================
// TODO: Fix the CSS to make this grid responsive
// Requirements:
// - Mobile (< 640px): 1 column
// - Tablet (>= 640px): 2 columns
// - Desktop (>= 1024px): 3 columns
// (Fix this in the CSS file!)
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
        {cards.map((c) => (
          <article key={c.id} className="card">
            <h4>{c.title}</h4>
            <p>{c.text}</p>
          </article>
        ))}
      </div>
      <p className="hint">
        Fix the .card-grid CSS to be responsive, and use .map() to render the
        cards!
      </p>
    </div>
  );
}

// ==================== EXERCISE 10: List Rendering with Keys ====================
// TODO: Render a list of items with proper keys
// Requirements:
// - Use .map() to render the todos
// - Each item needs a unique key prop
// - Show the todo text and a checkbox
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
        {todos.map((t) => (
          <li key={t.id} className={t.completed ? "completed" : ""}>
            <label>
              <input type="checkbox" defaultChecked={t.completed} /> {t.text}
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ==================== Main Worksheet Component ====================
function ReactWorksheet() {
  return (
    <div className="react-worksheet">
      <header className="worksheet-header">
        <h1>React Workshop Worksheet</h1>
        <p className="subtitle">
          🎉 Great job! You fixed the syntax errors in Exercise 1 and the
          website is now rendering!
        </p>
        <p className="subtitle">
          Now continue with the remaining exercises below.
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
            You successfully fixed all 4 JSX syntax errors! The button below
            should now work when clicked.
          </p>
          <WelcomeCard />
        </section>

        {/* Exercise 2 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">2</span>
            <h2>Use Props</h2>
          </div>
          <div className="book-grid">
            {/* TODO: Pass props to BookCard */}
            <BookCard />
            <BookCard />
            <BookCard />
          </div>
        </section>

        {/* Exercise 3 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">3</span>
            <h2>Fix State Management</h2>
          </div>
          <Counter />
        </section>

        {/* Exercise 4 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">4</span>
            <h2>Create Component with Props</h2>
          </div>
          <div className="product-grid">
            {/* TODO: Add ProductCard components with different props */}
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
            <h2>Interactive Toggle</h2>
          </div>
          <ToggleContent />
        </section>

        {/* Exercise 6 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">6</span>
            <h2>Controlled Form</h2>
          </div>
          <GreetingForm />
        </section>

        {/* Exercise 7 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">7</span>
            <h2>Responsive Navbar</h2>
          </div>
          <ResponsiveNavbar />
        </section>

        {/* Exercise 8 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">8</span>
            <h2>Responsive Button (CSS)</h2>
          </div>
          <ResponsiveButton />
        </section>

        {/* Exercise 9 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">9</span>
            <h2>Responsive Grid (CSS)</h2>
          </div>
          <CardGrid />
        </section>

        {/* Exercise 10 */}
        <section className="exercise">
          <div className="exercise-header">
            <span className="exercise-number">10</span>
            <h2>List Rendering</h2>
          </div>
          <TodoList />
        </section>
      </div>

      <footer className="worksheet-footer">
        <h2>Bonus Challenges</h2>
        <ul>
          <li>Add hover effects to all buttons</li>
          <li>Create a dark mode toggle component</li>
          <li>Build a simple calculator with useState</li>
          <li>Create a responsive image gallery</li>
        </ul>
      </footer>
    </div>
  );
}

export default ReactWorksheet;

import classNames from "classnames";
import "./Button.css";

export default function Button({
  className,
  styles,
  children,
  variant = "primary",
  onClick,
  ...props
}) {
  const buttonClass = classNames(
    "button", variant,
    className
  );

  return (
    <button
      className={`${buttonClass} ${styles}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}

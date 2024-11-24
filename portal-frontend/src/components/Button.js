import classNames from "classnames";
import "./Button.css";

export default function Button({
  className,
  styles,
  children,
  variant = "primary",
  onClick,
}) {
  const buttonClass = classNames(
    "button",
    {
      "button--primary": variant === "primary",
      "button--secondary": variant === "secondary",
    },
    className
  );

  return (
    <button
      className={`${buttonClass} ${styles}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

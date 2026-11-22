import "./SelectQuestion.css";
import React, {
  forwardRef,
  useEffect,
  useId,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import classNames from "classnames";

const MAX_VISIBLE_OPTIONS = 60;

const isEmpty = (value) =>
  Array.isArray(value) ? value.length === 0 : !value || value.trim() === "";

// Matches that start with the query rank above matches that only contain it.
const filterOptions = (options, query) => {
  const q = query.trim().toLowerCase();
  if (!q) return options;
  const starts = [];
  const contains = [];
  for (const option of options) {
    const lower = option.toLowerCase();
    if (lower.startsWith(q)) starts.push(option);
    else if (lower.includes(q)) contains.push(option);
  }
  return starts.concat(contains);
};

/**
 * Dropdown question.
 *
 * - `options`: an array of strings, or a function returning a Promise of one
 *   (loaded the first time the field is opened, for very long lists).
 * - `multiple`: lets the applicant pick several values; the answer is an array.
 * - `allowCustom`: offers "Use “…”" when the typed text isn't in the list.
 * - `searchable={false}`: renders a plain native <select> (short lists).
 */
export const SelectQuestion = forwardRef(
  (
    {
      name,
      label,
      options,
      formData,
      handleInputChange,
      required = false,
      firstTry,
      multiple = false,
      allowCustom = false,
      searchable = true,
      placeholder = "Select…",
      hint,
      fullWidth = false,
      isValid = (value) => !required || !isEmpty(value),
    },
    ref,
  ) => {
    const value = formData[name] ?? (multiple ? [] : "");
    const invalid = !firstTry && !isValid(value);

    useImperativeHandle(ref, () => ({
      isValid: () => isValid(formData[name] ?? (multiple ? [] : "")),
    }));

    const containerClass = classNames("question-container", "select-question", {
      "select-question-full": fullWidth || multiple,
    });

    const labelEl = (
      <label className="question-label" htmlFor={name}>
        {label}
        {required && <span className="required-mark">*</span>}
      </label>
    );
    const hintEl = hint && <span className="question-hint">{hint}</span>;

    if (!searchable) {
      const list = Array.isArray(options) ? options : [];
      return (
        <div className={containerClass}>
          {labelEl}
          <select
            id={name}
            name={name}
            className={classNames("question-input", "native-select", {
              "native-select-empty": !value,
              "invalid-border": invalid,
            })}
            value={value}
            onChange={(e) => handleInputChange(name, e.target.value)}
          >
            <option value="" disabled>
              {placeholder}
            </option>
            {list.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          {hintEl}
        </div>
      );
    }

    return (
      <div className={containerClass}>
        {labelEl}
        <Combobox
          id={name}
          value={value}
          onChange={(next) => handleInputChange(name, next)}
          options={options}
          multiple={multiple}
          allowCustom={allowCustom}
          placeholder={placeholder}
          invalid={invalid}
        />
        {hintEl}
      </div>
    );
  },
);

const Combobox = ({
  id,
  value,
  onChange,
  options,
  multiple,
  allowCustom,
  placeholder,
  invalid,
}) => {
  const listboxId = useId();
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [loaded, setLoaded] = useState(Array.isArray(options) ? options : null);

  // Lazily load long option lists the first time the dropdown opens.
  useEffect(() => {
    if (!open || loaded || typeof options !== "function") return;
    let cancelled = false;
    options().then((list) => {
      if (!cancelled) setLoaded(list);
    });
    return () => {
      cancelled = true;
    };
  }, [open, loaded, options]);

  const items = useMemo(() => {
    if (!loaded) return { list: [], more: 0 };
    const available = multiple
      ? loaded.filter((option) => !value.includes(option))
      : loaded;
    const matches = filterOptions(available, query);
    const list = matches.slice(0, MAX_VISIBLE_OPTIONS).map((option) => ({
      value: option,
      label: option,
    }));
    const typed = query.trim();
    const exact = loaded.some((o) => o.toLowerCase() === typed.toLowerCase());
    const alreadyChosen = multiple ? value.includes(typed) : value === typed;
    if (allowCustom && typed && !exact && !alreadyChosen) {
      list.push({ value: typed, label: `Use “${typed}”`, custom: true });
    }
    return { list, more: Math.max(0, matches.length - MAX_VISIBLE_OPTIONS) };
  }, [loaded, query, multiple, value, allowCustom]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current?.querySelector(`[data-index="${activeIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, open]);

  const choose = (option) => {
    if (multiple) {
      onChange([...value, option]);
      setQuery("");
      inputRef.current?.focus();
    } else {
      onChange(option);
      setQuery("");
      setOpen(false);
    }
  };

  const remove = (option) => {
    onChange(value.filter((v) => v !== option));
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (!open) setOpen(true);
        else setActiveIndex((i) => Math.min(i + 1, items.list.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
        if (open && items.list[activeIndex]) {
          e.preventDefault();
          choose(items.list[activeIndex].value);
        }
        break;
      case "Escape":
        setOpen(false);
        setQuery("");
        break;
      case "Backspace":
        if (multiple && !query && value.length) {
          onChange(value.slice(0, -1));
        }
        break;
      default:
    }
  };

  const showValueInInput = !multiple && !open;
  const activeOption = items.list[activeIndex];

  return (
    <div
      className={classNames("combo", { "combo-open": open })}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          setOpen(false);
          setQuery("");
        }
      }}
    >
      <div
        className={classNames("combo-control", {
          "invalid-border": invalid,
          "combo-control-multi": multiple,
        })}
        onMouseDown={(e) => {
          if (e.target !== inputRef.current) {
            e.preventDefault();
            inputRef.current?.focus();
            setOpen(true);
          }
        }}
      >
        {multiple &&
          value.map((option) => (
            <span className="combo-chip" key={option}>
              {option}
              <button
                type="button"
                className="combo-chip-remove"
                aria-label={`Remove ${option}`}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => remove(option)}
              >
                ×
              </button>
            </span>
          ))}
        <input
          ref={inputRef}
          id={id}
          className="combo-input"
          role="combobox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={
            open && activeOption ? `${listboxId}-${activeIndex}` : undefined
          }
          autoComplete="off"
          value={showValueInInput ? value : query}
          placeholder={
            multiple && value.length
              ? "Add another…"
              : !multiple && value
                ? value
                : placeholder
          }
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onClick={() => setOpen(true)}
          onKeyDown={handleKeyDown}
        />
        <span className="combo-caret" aria-hidden="true" />
      </div>
      {open && (
        <ul className="combo-menu" role="listbox" id={listboxId} ref={listRef}>
          {!loaded && <li className="combo-empty">Loading…</li>}
          {loaded && items.list.length === 0 && (
            <li className="combo-empty">No matches</li>
          )}
          {items.list.map((item, index) => (
            <li
              key={`${item.custom ? "custom:" : ""}${item.value}`}
              id={`${listboxId}-${index}`}
              data-index={index}
              role="option"
              aria-selected={!multiple && item.value === value}
              className={classNames("combo-option", {
                "combo-option-active": index === activeIndex,
                "combo-option-selected": !multiple && item.value === value,
                "combo-option-custom": item.custom,
              })}
              onMouseDown={(e) => e.preventDefault()}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => choose(item.value)}
            >
              {item.label}
            </li>
          ))}
          {items.more > 0 && (
            <li className="combo-empty">
              {items.more.toLocaleString()} more — keep typing to narrow down
            </li>
          )}
        </ul>
      )}
    </div>
  );
};

import './Question.css';

export const Question = ({ name, label, type = 'text', formData, handleInputChange }) => {
    return (
        <div className="question-container">
            <label className="question-label" htmlFor={name}>{label}</label>
            <input
                className="question-input"
                type={type}
                id={name}
                name={name}
                value={formData[name] || ''}
                onChange={e => handleInputChange(name, e.target.value)}
                required
            />
        </div>
    );
};

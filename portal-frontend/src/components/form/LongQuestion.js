import './LongQuestion.css';

export const LongQuestion = ({ name, label, formData, handleInputChange, rows }) => {
    return (
        <div className="long-container">
            <label className="long-label" htmlFor={name}>{label}</label>
            <textarea
                className="long-textarea"
                id={name}
                name={name}
                value={formData[name] || ''}
                onChange={e => handleInputChange(name, e.target.value)}
                rows={rows}
                required
            />
        </div>
    );
};

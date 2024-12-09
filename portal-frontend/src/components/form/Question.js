import './Form.css';

export const Question = ({ name, label, type = 'text', formData, handleInputChange }) => {
    return (
        <div>
            <label htmlFor={name} className="form-label">{label}</label>
            <input
                type={type}
                id={name}
                name={name}
                value={formData[name] || ''}
                onChange={e => handleInputChange(name, e.target.value)}
                required
                className="form-input"
            />
        </div>
    );
}
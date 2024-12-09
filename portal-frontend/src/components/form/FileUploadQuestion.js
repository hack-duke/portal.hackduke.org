import './FileUploadQuestion.css'

export const FileUploadQuestion = ({ name, label, accept, formData, handleFileChange }) => {
    return (
        <div>
            <label className="file-question-label" htmlFor={name}>{label}</label>
            <label className="file-question-button" htmlFor={name}>Choose File</label>
            <input
                id={name}
                type="file"
                accept={accept}
                onChange={e => handleFileChange(name, e.target.files[0])}
                required
            />
            <span className='file-question-name'>
                {formData?.[name] && formData[name].name}
            </span>
        </div>
    );
}

export const FileUploadQuestion = ({ name, label, accept, formData, handleFileChange }) => {
    return (
        <div>
            <label htmlFor={name}>{label}</label>
            <input
                id={name}
                type="file"
                accept={accept}
                onChange={e => handleFileChange(name, e.target.files[0])}
                required
            />
        </div>
    );
}

import './FullPageLoadingSpinner.css'
import CircularProgress from '@mui/material/CircularProgress';

export const FullPageLoadingSpinner = () => {
    return (
        <div className='wrapper'>
            <div>
                <CircularProgress
                    size={72}
                    thickness={5}
                />
            </div>
        </div>
    )
}
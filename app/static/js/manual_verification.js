/**
 * Manual account verification helper functions
 */

// Update the verification status UI based on API response
function updateVerificationStatusUI(data) {
    const statusContainer = document.getElementById('status-container');
    const successContainer = document.getElementById('success-container');
    const errorContainer = document.getElementById('error-container');
    const statusMessage = document.getElementById('status-message');
    const statusDetails = document.getElementById('status-details');
    const errorMessage = document.getElementById('error-message');
    
    if (!statusContainer || !successContainer || !errorContainer) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Update status message
    if (statusMessage) {
        statusMessage.textContent = getStatusText(data.status);
    }
    
    // Update status details
    if (statusDetails && data.error) {
        statusDetails.textContent = data.error;
    }
    
    // Handle completed verification
    if (data.is_verified) {
        statusContainer.classList.add('d-none');
        successContainer.classList.remove('d-none');
        errorContainer.classList.add('d-none');
    } 
    // Handle failed verification
    else if (data.status === 'failed') {
        statusContainer.classList.add('d-none');
        successContainer.classList.add('d-none');
        errorContainer.classList.remove('d-none');
        
        if (errorMessage) {
            errorMessage.textContent = data.error || 'Verification failed. Please try again.';
        }
    }
    // For all other statuses, show the status container
    else {
        statusContainer.classList.remove('d-none');
        successContainer.classList.add('d-none');
        errorContainer.classList.add('d-none');
    }
}

// Convert status code to user-friendly text
function getStatusText(status) {
    switch(status) {
        case 'pending':
            return 'Waiting to start verification...';
        case 'in_progress':
            return 'Verification in progress...';
        case 'manual_verification':
            return 'Manual verification in progress...';
        case 'manual_required':
            return 'Manual verification required';
        case 'completed':
            return 'Verification completed successfully';
        case 'failed':
            return 'Verification failed';
        default:
            return 'Checking status...';
    }
}

// Poll the server for verification status updates
function pollVerificationStatus(accountId, interval = 2000, maxAttempts = 150) {
    let attempts = 0;
    
    function checkStatus() {
        fetch(`/accounts/api/manual-verify-status/${accountId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Status update:', data);
                attempts++;
                
                // Update UI based on status
                updateVerificationStatusUI(data);
                
                // Determine if we should continue polling
                if (data.is_verified || data.status === 'failed') {
                    // Stop polling on success or failure
                    return;
                } else if (attempts >= maxAttempts) {
                    // Stop polling after max attempts reached (timeout)
                    const errorContainer = document.getElementById('error-container');
                    const errorMessage = document.getElementById('error-message');
                    const statusContainer = document.getElementById('status-container');
                    
                    if (errorContainer && errorMessage && statusContainer) {
                        statusContainer.classList.add('d-none');
                        errorContainer.classList.remove('d-none');
                        errorMessage.textContent = 'Verification timed out. Please try again.';
                    }
                    return;
                }
                
                // Continue polling
                setTimeout(checkStatus, interval);
            })
            .catch(error => {
                console.error('Error checking status:', error);
                // Continue polling despite errors, but with a longer interval
                setTimeout(checkStatus, interval * 2);
            });
    }
    
    // Start polling
    checkStatus();
}

// Initialize verification status polling when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const verificationStatusContainer = document.getElementById('verification-status-container');
    
    if (verificationStatusContainer) {
        const accountId = verificationStatusContainer.dataset.accountId;
        if (accountId) {
            pollVerificationStatus(accountId);
        } else {
            console.error('Account ID not found in verification status container');
        }
    }
});
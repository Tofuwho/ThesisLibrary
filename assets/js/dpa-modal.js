/**
 * DPA Modal Handler Module
 * Handles Data Privacy Act confirmation modal for thesis downloads
 * 
 * This module provides functions to:
 * - Show/hide DPA confirmation modal
 * - Handle download confirmation with privacy compliance
 * - Store download intent and proceed with actual download
 */

// Global variable to store the thesis ID for download
let pendingDownloadThesisId = null;

/**
 * Shows the DPA confirmation modal for thesis download
 * 
 * @param {number} thesisId - The ID of the thesis to download
 */
function showDpaModal(thesisId) {
    console.log('DPA Modal: Showing DPA confirmation for thesis ID:', thesisId);
    
    // Store the thesis ID for later use
    pendingDownloadThesisId = thesisId;
    
    // Get modal element
    const dpaModal = document.getElementById('dpaModal');
    
    if (dpaModal) {
        // Show modal and prevent body scrolling
        dpaModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Focus on the confirm button for accessibility
        const confirmButton = dpaModal.querySelector('.dpa-btn-confirm');
        if (confirmButton) {
            setTimeout(() => {
                confirmButton.focus();
            }, 100);
        }
        
        console.log('DPA Modal: Modal displayed successfully');
    } else {
        console.error('DPA Modal: Modal element not found!');
    }
}

/**
 * Hides the DPA confirmation modal and restores body scrolling
 */
function hideDpaModal() {
    console.log('DPA Modal: Hiding DPA confirmation modal');
    
    const dpaModal = document.getElementById('dpaModal');
    if (dpaModal) {
        dpaModal.classList.add('hidden');
        document.body.style.overflow = '';
        
        // Clear the pending download ID
        //pendingDownloadThesisId = null;
        
        console.log('DPA Modal: Modal hidden successfully');
    }
}

/**
 * Proceeds with the download after DPA confirmation
 * This function is called when user clicks "I Agree & Download"
 */
function proceedWithDownload() {
    console.log('DPA Modal: User confirmed DPA, proceeding with download');
    if (pendingDownloadThesisId) {
        hideDpaModal();
        console.log('DPA Modal: Initiating download for thesis ID:', pendingDownloadThesisId);
        window.location.href = `/thesis/${pendingDownloadThesisId}/download/`;
        pendingDownloadThesisId = null; // Clear it here
    } else {
        console.error('DPA Modal: No pending download ID found!');
        hideDpaModal();
    }
}

/**
 * Enhanced download handler that shows DPA modal for authenticated users
 * This replaces the direct download for authenticated users
 * 
 * @param {number} thesisId - The ID of the thesis to download
 */
function handleAuthenticatedDownload(thesisId) {
    console.log('DPA Modal: Handling authenticated download for thesis ID:', thesisId);
    
    // Show DPA confirmation modal instead of direct download
    showDpaModal(thesisId);
}

/**
 * Initialize DPA modal functionality
 * Sets up event listeners and keyboard navigation
 */
function initializeDpaModal() {
    console.log('DPA Modal: Initializing DPA modal functionality');
    
    // Add keyboard event listeners for accessibility
    document.addEventListener('keydown', function(event) {
        const dpaModal = document.getElementById('dpaModal');
        
        // Only handle keyboard events when modal is visible
        if (dpaModal && !dpaModal.classList.contains('hidden')) {
            // ESC key to close modal
            if (event.key === 'Escape') {
                hideDpaModal();
            }
            
            // Enter key on confirm button
            if (event.key === 'Enter' && event.target.classList.contains('dpa-btn-confirm')) {
                proceedWithDownload();
            }
        }
    });
    
    // Add click outside to close functionality
    const dpaModal = document.getElementById('dpaModal');
    if (dpaModal) {
        const overlay = dpaModal.querySelector('.dpa-modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', hideDpaModal);
        }
    }
    
    console.log('DPA Modal: DPA modal functionality initialized');
}

// Initialize DPA modal when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeDpaModal);

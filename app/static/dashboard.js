// --- Configuration ---
const API_URL = '/api/v1/jobs'; 
// ⚠️ CHUCK NORRIS NOTE: This token is MOCKED. If you see auth errors, the issue is often here, 
// or the backend isn't accepting it. This needs to be pulled from the real login flow.
const MOCK_AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYTIzYTlkZC0wNzE5LTQ5NmYtODA0Zi01NDY1YzMxMjlmMDMiLCJzY29wZXMiOlsiYmFzaWMiXSwiaWF0IjoxNzYwNTMyMDkzLCJleHAiOjE3NjA1MzI5OTMsInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiIwODI3NDkwZC1iY2E4LTQzNDktYjY5My0wODQyMjhjMzZlZWUifQ.Wt0ggSSFwZU39-VUCs_f97P_BTisBgAqENhTFxzuIMA";

// --- DOM Elements ---
// Ensure the elements exist in dashboard.html
const jobTableBody = document.getElementById('jobTableBody');
const jobListMobile = document.getElementById('jobListMobile');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorIndicator = document.getElementById('errorIndicator');
const refreshButton = document.getElementById('refreshButton');
const refreshSpinner = document.getElementById('refreshSpinner');
const refreshText = document.getElementById('refreshText');
const backButton = document.getElementById('backButton');
const jobListView = document.getElementById('jobListView');
const jobDetailView = document.getElementById('jobDetailView');
const detailJobId = document.getElementById('detailJobId');
const detailContent = document.getElementById('detailContent');
const copyJobIdButton = document.getElementById('copyJobIdButton');
const copyButtonText = document.getElementById('copyButtonText');

// --- State Management ---
let allJobs = [];
let currentView = 'list'; // 'list' or 'detail'

// --- Utility Functions ---

/**
 * Determines the Tailwind classes for the status pill based on the job status.
 */
function getStatusClasses(status) {
    const normalizedStatus = status.toUpperCase();
    switch (normalizedStatus) {
        case 'COMPLETED':
            return 'bg-green-100 text-green-800';
        case 'FAILED':
        case 'ERROR':
            return 'bg-red-100 text-red-800';
        case 'IN_PROGRESS':
        case 'RUNNING':
            return 'bg-blue-100 text-blue-800 animate-pulse';
        case 'PENDING (SHIM)': // Mock status, treat as Pending/Queued
        case 'PENDING':
        case 'QUEUED':
        default:
            return 'bg-yellow-100 text-yellow-800';
    }
}

/**
 * Navigates the view between list and detail.
 */
function setView(view, jobId = null) {
    currentView = view;
    if (view === 'list') {
        jobListView.classList.remove('hidden');
        jobDetailView.classList.add('hidden');
        // Refresh list when returning to list view
        fetchJobs(); 
    } else if (view === 'detail' && jobId) {
        jobListView.classList.add('hidden');
        jobDetailView.classList.remove('hidden');
        renderJobDetail(jobId);
    }
}

/**
 * Renders a single job as a table row for desktop view.
 */
function renderTableRow(job) {
    const statusClasses = getStatusClasses(job.status);
    const statusPill = `<span class="status-pill ${statusClasses}">${job.status}</span>`;
    
    return `
        <tr class="hover:bg-gray-50 transition duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-mono">
                <span class="job-id-link" data-job-id="${job.id}">${job.id.substring(0, 8)}...</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 truncate max-w-xs">
                ${job.title}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${job.owner_email}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                ${statusPill}
            </td>
        </tr>
    `;
}

/**
 * Renders a single job as a mobile card for mobile view.
 */
function renderMobileCard(job) {
    const statusClasses = getStatusClasses(job.status);
    const statusPill = `<span class="status-pill ${statusClasses}">${job.status}</span>`;

    return `
        <div class="bg-gray-50 p-4 rounded-lg shadow-sm border border-gray-200">
            <div class="flex justify-between items-start mb-2">
                <span class="text-xs font-mono text-indigo-600 job-id-link" data-job-id="${job.id}">${job.id.substring(0, 12)}...</span>
                ${statusPill}
            </div>
            <p class="text-base font-semibold text-gray-900 mb-1">${job.title}</p>
            <p class="text-sm text-gray-500">Owner: <span class="font-medium">${job.owner_email}</span></p>
        </div>
    `;
}

/**
 * Copies the full job ID to the clipboard and gives feedback.
 */
function copyJobIdToClipboard(jobId) {
    // document.execCommand('copy', false, jobId);
    // Use modern API with fallback for better practice
    if (navigator.clipboard) {
        navigator.clipboard.writeText(jobId).then(() => {
            copyButtonText.textContent = 'Copied! ✅';
            setTimeout(() => {
                copyButtonText.textContent = 'Copy ID';
            }, 2000);
        }).catch(err => {
            console.error('Could not copy text: ', err);
            copyButtonText.textContent = 'Copy Failed';
            setTimeout(() => {
                copyButtonText.textContent = 'Copy ID';
            }, 2000);
        });
    } else {
        // Fallback for document.execCommand in case navigator.clipboard is restricted
        const tempInput = document.createElement('input');
        tempInput.value = jobId;
        document.body.appendChild(tempInput);
        tempInput.select();
        try {
            document.execCommand('copy');
            copyButtonText.textContent = 'Copied! ✅';
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            copyButtonText.textContent = 'Copy Failed';
        }
        document.body.removeChild(tempInput);
        setTimeout(() => {
            copyButtonText.textContent = 'Copy ID';
        }, 2000);
    }
}

/**
 * Renders the detailed view for a selected job.
 */
function renderJobDetail(jobId) {
    const job = allJobs.find(j => j.id === jobId);
    
    if (!job) {
        detailJobId.textContent = 'Not Found';
        detailContent.innerHTML = `<p class="text-red-500 mt-4">Could not find job with ID: ${jobId}</p>`;
        return;
    }

    detailJobId.textContent = job.id;
    // Attach copy listener immediately
    copyJobIdButton.onclick = () => copyJobIdToClipboard(job.id);

    const statusClasses = getStatusClasses(job.status);
    const statusPill = `<span class="status-pill text-base ${statusClasses}">${job.status}</span>`;
    
    // Format JSON result content nicely
    let resultContentHtml;
    try {
        const result = job.result_content ? JSON.parse(job.result_content) : null;
        if (result) {
            resultContentHtml = `
                <pre class="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto border border-gray-300 shadow-inner max-h-96">${JSON.stringify(result, null, 2)}</pre>
            `;
        } else {
            resultContentHtml = '<p class="text-gray-500 italic">No structured result content available.</p>';
        }
    } catch (e) {
        resultContentHtml = `<p class="text-red-500 italic">Error parsing result content JSON: ${job.result_content}</p>`;
    }

    // Build the detail HTML
    detailContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="bg-gray-50 p-4 rounded-lg border">
                <h3 class="text-lg font-semibold text-gray-700 mb-2">Job Metadata</h3>
                <p class="text-sm"><span class="font-medium">Title:</span> ${job.title}</p>
                <p class="text-sm"><span class="font-medium">Owner:</span> ${job.owner_email}</p>
                <p class="text-sm"><span class="font-medium">Status:</span> ${statusPill}</p>
                <p class="text-sm"><span class="font-medium">Created At:</span> ${job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}</p>
            </div>
            
            <div class="bg-gray-50 p-4 rounded-lg border">
                <h3 class="text-lg font-semibold text-gray-700 mb-2">Timing & Results</h3>
                <p class="text-sm"><span class="font-medium">Started At:</span> ${job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}</p>
                <p class="text-sm"><span class="font-medium">Finished At:</span> ${job.finished_at ? new Date(job.finished_at).toLocaleString() : 'N/A'}</p>
                <p class="text-sm break-words"><span class="font-medium">MinIO Result Key:</span> ${job.result_path || '<span class="italic text-gray-400">Not yet available</span>'}</p>
                <p class="text-sm"><span class="font-medium">Input Key:</span> ${job.payload?.input_key || '<span class="italic text-gray-400">N/A</span>'}</p>
            </div>
        </div>

        <h3 class="text-xl font-semibold text-gray-900 mb-3">Result Content Payload</h3>
        <div class="bg-white p-4 rounded-lg">
            ${resultContentHtml}
        </div>
    `;
}

/**
 * Attaches click handlers to the newly rendered job ID links.
 */
function attachJobLinkListeners() {
    document.querySelectorAll('.job-id-link').forEach(link => {
        link.addEventListener('click', (event) => {
            const jobId = event.target.getAttribute('data-job-id');
            if (jobId) {
                setView('detail', jobId);
            }
        });
    });
}


// --- Main Fetch and Render Logic ---

/**
 * Fetches job data from the API and renders it to the dashboard.
 */
async function fetchJobs() {
    // Check if DOM elements are available before operating
    if (!jobTableBody) {
        console.error("DOM not fully loaded, skipping fetchJobs.");
        return;
    }
    jobTableBody.innerHTML = ''; 
    jobListMobile.innerHTML = '';
    loadingIndicator.classList.remove('hidden');
    errorIndicator.classList.add('hidden');
    refreshButton.disabled = true;
    refreshSpinner.classList.remove('hidden');
    refreshText.textContent = 'Loading...';
    
    try {
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${MOCK_AUTH_TOKEN}` 
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        allJobs = await response.json(); // Store all jobs in state
        
        if (allJobs.length === 0) {
            jobTableBody.innerHTML = '<tr><td colspan="4" class="text-center py-6 text-gray-400">No active jobs found.</td></tr>';
            jobListMobile.innerHTML = '<p class="text-center py-6 text-gray-400">No active jobs found.</p>';
            return;
        }

        // Render for Desktop Table
        allJobs.forEach(job => {
            jobTableBody.innerHTML += renderTableRow(job);
        });

        // Render for Mobile Cards
        allJobs.forEach(job => {
            jobListMobile.innerHTML += renderMobileCard(job);
        });

        attachJobLinkListeners(); // Attach listeners after rendering
        
    } catch (error) {
        console.error("Error fetching jobs:", error);
        errorIndicator.classList.remove('hidden');
    } finally {
        loadingIndicator.classList.add('hidden');
        refreshButton.disabled = false;
        refreshSpinner.classList.add('hidden');
        refreshText.textContent = 'Refresh Jobs';
    }
}

// --- Event Listeners and Initialization ---

// Since the script runs after the DOM is ready (it's loaded at the end of the body in base.html)

if (refreshButton && backButton) {
    // Attach event listener to the refresh button
    refreshButton.addEventListener('click', () => setView('list'));

    // Attach event listener to the back button in the detail view
    backButton.addEventListener('click', () => setView('list'));
    
    // Initial load: Start on the list view
    setView('list'); 
} else {
    // Fallback in case the script loads before the elements are available for some reason
    document.addEventListener('DOMContentLoaded', () => {
        refreshButton.addEventListener('click', () => setView('list'));
        backButton.addEventListener('click', () => setView('list'));
        setView('list');
    });
}

/* API boundary for the production frontend. Records are persisted by FastAPI/PostgreSQL. */

const API_BASE_URL = window.SCHOOL_API_URL || "http://localhost:8000/api/v1";

async function apiRequest(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = sessionStorage.getItem("school_access_token");
    if (token) headers.Authorization = `Bearer ${token}`;
    if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";

    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers,
        ...options
    });

    if (!response.ok) {
        let detail = `API request failed: ${response.status}`;
        try {
            const errorBody = await response.json();
            detail = errorBody.detail || detail;
        } catch {
            // Keep the status-based message when the server did not return JSON.
        }
        const error = new Error(detail);
        error.status = response.status;
        throw error;
    }

    return response.status === 204 ? null : response.json();
}

// These small functions become the single frontend entry point for database-backed data.
window.schoolApi = {
    health: () => apiRequest("/health"),
    listSchools: () => apiRequest("/schools"),
    login: (payload) => apiRequest("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
    submitApplication: (formData) => apiRequest("/applications", { method: "POST", body: formData }),
    listApplications: () => apiRequest("/applications"),
    updateApplicationStatus: (id, status) => apiRequest(`/applications/${id}/status`, {
        method: "PATCH", body: JSON.stringify({ status })
    }),
    submitAssessment: (payload) => apiRequest("/assessments/submit", {
        method: "POST", body: JSON.stringify(payload)
    }),
    listAssessmentResults: () => apiRequest("/assessments/results")
};


// Define types for SEBI data
export interface SEBIExcelSummary {
    id: number;
    date_key: string;
    row_index: number;
    pdf_link: string;
    summary: string;
    inserted_at: string;
}

const API_BASE_URL = '';

// Helper to handle fetch with timeout
const fetchWithTimeout = async (url: string, timeoutMs: number = 15000): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error instanceof Error && error.name === 'AbortError') {
            throw new Error(`Request timeout - server is taking too long to respond (${timeoutMs / 1000} seconds elapsed)`);
        }
        throw error;
    }
};

// Helper to handle response validation
const handleResponse = async (response: Response, errorMessagePrefix: string) => {
    if (!response.ok) {
        let errorMessage = `${errorMessagePrefix}: ${response.status} ${response.statusText}`;
        try {
            const errorText = await response.text();
            if (errorText) {
                errorMessage = errorText;
            }
        } catch (e) {
            // If we can't parse the error text, use the default message
        }
        throw new Error(errorMessage);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Received non-JSON response from server');
    }

    return response.json();
};

export const sebiService = {
    // Fetch SEBI data from API
    fetchSEBIData: async (limit: number = 100, offset: number = 0): Promise<any> => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/sebi-analysis-data?limit=${limit}&offset=${offset}`);
        return handleResponse(response, 'Failed to fetch SEBI data');
    }
};

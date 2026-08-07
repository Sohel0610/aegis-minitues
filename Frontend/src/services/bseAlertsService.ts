
// Define types for workbook data
export interface ExcelData {
    [key: string]: string | number;
}

export interface CombinedWorkbookData {
    file_name: string;
    sheets: string[];
    combined_data: ExcelData[];
    count: number;
    special_sheets_excluded: string[];
}

export interface SpecialSheetsData {
    trend_data: ExcelData[];
    weekly_trend_data: ExcelData[];
    monthly_summary_data: ExcelData[];
    trend_columns: string[];
    weekly_trend_columns: string[];
    monthly_summary_columns: string[];
}

const API_BASE_URL = '/api';

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

export const bseAlertsService = {
    // Fetch combined workbook data from API
    fetchCombinedWorkbookData: async (fileName: string): Promise<CombinedWorkbookData> => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/combined-workbook-data/${fileName}`);
        return handleResponse(response, 'Failed to fetch combined workbook data');
    },

    // Fetch special sheets data from API
    fetchSpecialSheetsData: async (fileName: string): Promise<SpecialSheetsData> => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/special-sheets-data/${fileName}`);
        return handleResponse(response, 'Failed to fetch special sheets data');
    },

    // Fetch BSE alerts data from the new database endpoint
    fetchBSEAlertsData: async (limit: number = 100, offset: number = 0): Promise<any> => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/bse-alerts?limit=${limit}&offset=${offset}`);
        return handleResponse(response, 'Failed to fetch BSE alerts data');
    }
};

// Base URL for API requests - can be overridden with environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

// Generic API request function with error handling
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  // Add authentication if needed in the future
  // const token = localStorage.getItem('auth_token');
  // if (token) {
  //   defaultHeaders['Authorization'] = `Bearer ${token}`;
  // }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(errorData.message || `API Error: ${response.status}`);
    }
    
    return await response.json() as T;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Dashboard API
export const dashboardAPI = {
  getLastStudySession: () => 
    apiRequest<{
      id: number;
      group_id: number;
      created_at: string;
      study_activity_id: number;
      group_name: string;
    }>('/dashboard/last-study-session'),
  
  getStudyProgress: () => 
    apiRequest<{
      total_words_studied: number;
      total_available_words: number;
    }>('/dashboard/study-progress'),
  
  getQuickStats: () => 
    apiRequest<{
      total_words: number;
      total_groups: number;
      words_mastered: number;
      recent_accuracy: number;
    }>('/dashboard/quick-stats'),
};

// Study Activities API
export const studyActivitiesAPI = {
  getAll: () => 
    apiRequest<Array<{
      id: number;
      name: string;
      thumbnail: string;
      description: string;
    }>>('/study_activities'),
  
  getById: (id: number) => 
    apiRequest<{
      id: number;
      name: string;
      thumbnail: string;
      description: string;
    }>(`/study_activities/${id}`),
  
  getSessions: (id: number) => 
    apiRequest<Array<{
      id: number;
      activity_name: string;
      group_name: string;
      start_time: string;
      end_time: string;
      review_items_count: number;
    }>>(`/study_activities/${id}/study_sessions`),
  
  launch: (id: number, groupId: number) => 
    apiRequest<{ redirect_url: string }>(`/study_activities/${id}/launch`, {
      method: 'POST',
      body: JSON.stringify({ group_id: groupId }),
    }),
};

// Words API
export const wordsAPI = {
  getAll: (page = 1) => 
    apiRequest<{
      words: Array<{
        id: number;
        japanese: string;
        romaji: string;
        english: string;
        correct_count: number;
        wrong_count: number;
      }>;
      total_pages: number;
      current_page: number;
    }>(`/words?page=${page}`),
  
  getById: (id: number) => 
    apiRequest<{
      id: number;
      japanese: string;
      romaji: string;
      english: string;
      correct_count: number;
      wrong_count: number;
      groups: Array<{
        id: number;
        name: string;
      }>;
    }>(`/words/${id}`),
};

// Groups API
export const groupsAPI = {
  getAll: (page = 1) => 
    apiRequest<Array<{
      id: number;
      name: string;
      word_count: number;
    }>>(`/groups?page=${page}`),
  
  getById: (id: number) => 
    apiRequest<{
      id: number;
      name: string;
      word_count: number;
    }>(`/groups/${id}`),
  
  getWords: (id: number, page = 1) => 
    apiRequest<Array<{
      id: number;
      japanese: string;
      romaji: string;
      english: string;
      correct_count: number;
      wrong_count: number;
    }>>(`/groups/${id}/words?page=${page}`),
  
  getStudySessions: (id: number, page = 1) => 
    apiRequest<Array<{
      id: number;
      activity_name: string;
      start_time: string;
      end_time: string;
      review_items_count: number;
    }>>(`/groups/${id}/study_sessions?page=${page}`),
};

// Study Sessions API
export const studySessionsAPI = {
  getAll: (page = 1) => 
    apiRequest<Array<{
      id: number;
      activity_name: string;
      group_name: string;
      start_time: string;
      end_time: string;
      review_items_count: number;
    }>>(`/study_sessions?page=${page}`),
  
  getById: (id: number) => 
    apiRequest<{
      id: number;
      activity_name: string;
      group_name: string;
      start_time: string;
      end_time: string;
      review_items_count: number;
    }>(`/study_sessions/${id}`),
  
  getWords: (id: number, page = 1) => 
    apiRequest<Array<{
      id: number;
      japanese: string;
      romaji: string;
      english: string;
      correct: boolean;
      review_time: string;
    }>>(`/study_sessions/${id}/words?page=${page}`),
};

// Settings API
export const settingsAPI = {
  resetHistory: () => 
    apiRequest<{ success: boolean }>('/reset_history', {
      method: 'POST',
    }),
  
  fullReset: () => 
    apiRequest<{ success: boolean }>('/full_reset', {
      method: 'POST',
    }),
}; 
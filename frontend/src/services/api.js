/**
 * API Service - Backend communication layer with authentication
 */

import { supabase } from '../lib/supabase';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth headers with current user token
async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    throw new Error('Not authenticated');
  }

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`
  };
}

// Helper function for fetch with error handling and auth
async function apiCall(endpoint, options = {}) {
  try {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        ...headers,
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error);
    throw error;
  }
}

// API Methods
export const api = {
  // Health check (no auth required)
  async healthCheck() {
    return fetch(`${API_BASE}/`).then(r => r.json());
  },

  // Get session state
  async getSession() {
    return apiCall('/session');
  },

  // Setup - Generate learning path
  async setup(learningGoal, userContext = '') {
    return apiCall('/setup', {
      method: 'POST',
      body: JSON.stringify({
        learning_goal: learningGoal,
        user_context: userContext,
      }),
    });
  },

  // Approve learning path and generate challenges
  async approvePath(learningPath) {
    return apiCall('/path/approve', {
      method: 'POST',
      body: JSON.stringify({
        learning_path: learningPath,
      }),
    });
  },

  // Adjust learning path based on user feedback
  async adjustPath(learningPath, userFeedback) {
    return apiCall('/path/adjust', {
      method: 'POST',
      body: JSON.stringify({
        learning_path: learningPath,
        user_feedback: userFeedback,
      }),
    });
  },

  // Get progress
  async getProgress() {
    return apiCall('/progress');
  },

  // Get all challenges metadata (titles, descriptions)
  async getChallengesMetadata() {
    return apiCall('/challenges/metadata');
  },

  // Start a lesson (Mastery Engine)
  async startLesson(moduleNumber, challengeNumber) {
    return apiCall('/lesson/start', {
      method: 'POST',
      body: JSON.stringify({
        module_number: moduleNumber,
        challenge_number: challengeNumber,
      }),
    });
  },

  // Respond to a lesson (Mastery Engine)
  async respondToLesson(moduleNumber, challengeNumber, userInput) {
    return apiCall('/lesson/respond', {
      method: 'POST',
      body: JSON.stringify({
        module_number: moduleNumber,
        challenge_number: challengeNumber,
        user_input: userInput,
      }),
    });
  },

  // Get source attributions for a lesson (Trust Layer)
  // Call this in parallel with startLesson for best performance
  async getLessonSources(moduleNumber, challengeNumber) {
    return apiCall('/lesson/sources', {
      method: 'POST',
      body: JSON.stringify({
        module_number: moduleNumber,
        challenge_number: challengeNumber,
      }),
    });
  },

  // Admin: Get statistics
  async getAdminStats() {
    return apiCall('/admin/stats');
  },

  // Reset user data (learning path, progress)
  async reset() {
    return apiCall('/reset', {
      method: 'POST',
    });
  },
};

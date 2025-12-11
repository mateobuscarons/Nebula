/**
 * API Service - Backend communication layer
 * Base URL: http://localhost:8000
 */

const API_BASE = 'http://localhost:8000';

// Helper function for fetch with error handling
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
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
  // Health check
  async healthCheck() {
    return apiCall('/');
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

  // Reset system (for testing)
  async reset() {
    return apiCall('/reset', { method: 'DELETE' });
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
};

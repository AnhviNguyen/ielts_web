import apiClient from '@/api/client.js'

export const adminService = {
  getOverview() {
    return apiClient.get('/admin/overview').then(r => r.data)
  },

  listUsers(params = {}) {
    return apiClient.get('/admin/users', { params }).then(r => r.data)
  },

  getUser(id) {
    return apiClient.get(`/admin/users/${id}`).then(r => r.data)
  },

  updateUserStatus(id, body) {
    return apiClient.patch(`/admin/users/${id}/status`, body).then(r => r.data)
  },

  resetXpStreak(id, body) {
    return apiClient.post(`/admin/users/${id}/reset-xp-streak`, body).then(r => r.data)
  },

  updateLeaderboard(id, body) {
    return apiClient.patch(`/admin/users/${id}/leaderboard`, body).then(r => r.data)
  },

  listLeaderboard(params = {}) {
    return apiClient.get('/admin/leaderboard', { params }).then(r => r.data)
  },

  listAnomalies() {
    return apiClient.get('/admin/leaderboard/anomalies').then(r => r.data)
  },

  listSystemVocabTopics(params = {}) {
    return apiClient.get('/admin/system-vocab/topics', { params }).then(r => r.data)
  },

  createSystemVocabTopic(body) {
    return apiClient.post('/admin/system-vocab/topics', body).then(r => r.data)
  },

  getSystemVocabTopic(id) {
    return apiClient.get(`/admin/system-vocab/topics/${id}`).then(r => r.data)
  },

  updateSystemVocabTopic(id, body) {
    return apiClient.patch(`/admin/system-vocab/topics/${id}`, body).then(r => r.data)
  },

  deleteSystemVocabTopic(id) {
    return apiClient.delete(`/admin/system-vocab/topics/${id}`).then(r => r.data)
  },

  createSystemVocabWord(topicId, body) {
    return apiClient.post(`/admin/system-vocab/topics/${topicId}/words`, body).then(r => r.data)
  },

  updateSystemVocabWord(topicId, wordId, body) {
    return apiClient.patch(`/admin/system-vocab/topics/${topicId}/words/${wordId}`, body).then(r => r.data)
  },

  deleteSystemVocabWord(topicId, wordId) {
    return apiClient.delete(`/admin/system-vocab/topics/${topicId}/words/${wordId}`).then(r => r.data)
  },

  copySystemVocabToUser(topicId, body) {
    return apiClient.post(`/admin/system-vocab/topics/${topicId}/copy-to-user`, body).then(r => r.data)
  },

  listWritingTopics(params = {}) {
    return apiClient.get('/admin/content/writing-topics', { params }).then(r => r.data)
  },

  getWritingTopic(id) {
    return apiClient.get(`/admin/content/writing-topics/${id}`).then(r => r.data)
  },

  createWritingTopic(rawJson) {
    return apiClient.post('/admin/content/writing-topics', { raw_json: rawJson }).then(r => r.data)
  },

  updateWritingTopic(id, rawJson) {
    return apiClient.patch(`/admin/content/writing-topics/${id}`, { raw_json: rawJson }).then(r => r.data)
  },

  archiveWritingTopic(id) {
    return apiClient.delete(`/admin/content/writing-topics/${id}`).then(r => r.data)
  },

  listMockTests(params = {}) {
    return apiClient.get('/admin/content/mock-tests', { params }).then(r => r.data)
  },

  getMockTest(id) {
    return apiClient.get(`/admin/content/mock-tests/${id}`).then(r => r.data)
  },

  createMockTest(rawJson) {
    return apiClient.post('/admin/content/mock-tests', { raw_json: rawJson }).then(r => r.data)
  },

  updateMockTest(id, rawJson) {
    return apiClient.patch(`/admin/content/mock-tests/${id}`, { raw_json: rawJson }).then(r => r.data)
  },

  archiveMockTest(id) {
    return apiClient.delete(`/admin/content/mock-tests/${id}`).then(r => r.data)
  },

  uploadAdminImage(file) {
    const body = new FormData()
    body.append('file', file)
    return apiClient.post('/admin/assets/images', body, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  uploadAdminAudio(file) {
    const body = new FormData()
    body.append('file', file)
    return apiClient.post('/admin/assets/audio', body, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  createReadingMockTestBuilder(body) {
    return apiClient.post('/admin/content/reading-mock-tests', body).then(r => r.data)
  },

  getReadingMockTestBuilder(id) {
    return apiClient.get(`/admin/content/reading-mock-tests/${id}/builder`).then(r => r.data)
  },

  updateReadingMockTestBuilder(id, body) {
    return apiClient.patch(`/admin/content/reading-mock-tests/${id}`, body).then(r => r.data)
  },

  createListeningMockTestBuilder(body) {
    return apiClient.post('/admin/content/listening-mock-tests', body).then(r => r.data)
  },

  getListeningMockTestBuilder(id) {
    return apiClient.get(`/admin/content/listening-mock-tests/${id}/builder`).then(r => r.data)
  },

  updateListeningMockTestBuilder(id, body) {
    return apiClient.patch(`/admin/content/listening-mock-tests/${id}`, body).then(r => r.data)
  },

  createSpeakingMockTestBuilder(body) {
    return apiClient.post('/admin/content/speaking-mock-tests', body).then(r => r.data)
  },

  getSpeakingMockTestBuilder(id) {
    return apiClient.get(`/admin/content/speaking-mock-tests/${id}/builder`).then(r => r.data)
  },

  updateSpeakingMockTestBuilder(id, body) {
    return apiClient.patch(`/admin/content/speaking-mock-tests/${id}`, body).then(r => r.data)
  },

  listQuizzes(params = {}) {
    return apiClient.get('/admin/content/quizzes', { params }).then(r => r.data)
  },

  getQuiz(id) {
    return apiClient.get(`/admin/content/quizzes/${id}`).then(r => r.data)
  },

  createQuiz(rawJson) {
    return apiClient.post('/admin/content/quizzes', { raw_json: rawJson }).then(r => r.data)
  },

  updateQuiz(id, rawJson) {
    return apiClient.patch(`/admin/content/quizzes/${id}`, { raw_json: rawJson }).then(r => r.data)
  },

  archiveQuiz(id) {
    return apiClient.delete(`/admin/content/quizzes/${id}`).then(r => r.data)
  },
}

/**
 * leaderboardService.js — top users by XP + current user rank.
 */
import apiClient from '@/api/client.js'

export class LeaderboardService {
  /**
   * @param {number} top — number of top entries (default 10)
   * @returns {Promise<{ top, current_user_rank, current_user }>}
   */
  async getLeaderboard(top = 10) {
    const { data } = await apiClient.get('/leaderboard', { params: { top } })
    return data
  }
}

export const leaderboardService = new LeaderboardService()

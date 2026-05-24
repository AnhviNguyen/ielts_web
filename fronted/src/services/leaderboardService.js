/**
 * leaderboardService.js — top users by XP + current user rank.
 */
import apiClient from '@/api/client.js'

export class LeaderboardService {
  /**
   * @param {number} top — number of top entries (default 10)
   * @returns {Promise<{ top, current_user_rank, current_user }>}
   */
  /**
   * @param {number} top
   * @param {'all'|'weekly'|'monthly'} period
   */
  async getLeaderboard(top = 10, period = 'all') {
    const { data } = await apiClient.get('/leaderboard', { params: { top, period } })
    return data
  }
}

export const leaderboardService = new LeaderboardService()

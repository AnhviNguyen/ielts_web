/**
 * src/services/leaderboardService.js
 * ─────────────────────────────────────
 * Service layer cho leaderboard — tuân theo DIP (SOLID):
 * Components không gọi API trực tiếp, chỉ gọi qua service.
 */
import apiClient from '@/api/client.js'

export class LeaderboardService {
  /** Lấy bảng xếp hạng top N users theo XP */
  async getLeaderboard(limit = 50) {
    const { data } = await apiClient.get('/leaderboard', { params: { limit } })
    return data
  }
}

export const leaderboardService = new LeaderboardService()

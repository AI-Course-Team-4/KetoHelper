import { api } from '@/hooks/useApi'

// ==========================================
// 타입 정의
// ==========================================

export interface AllergyMaster {
  id: number
  name: string
  description?: string
  category?: string
  severity_level: number
}

export interface DislikeMaster {
  id: number
  name: string
  description?: string
  category?: string
}

export interface UserProfile {
  id: string
  email: string
  nickname?: string
  profile_image_url?: string
  goals_kcal?: number
  goals_carbs_g?: number
  selected_allergy_ids: number[]
  selected_dislike_ids: number[]
  allergy_names: string[]
  dislike_names: string[]
}

export interface UserProfileUpdate {
  nickname?: string
  goals_kcal?: number
  goals_carbs_g?: number
  selected_allergy_ids?: number[]
  selected_dislike_ids?: number[]
}

// ==========================================
// API 서비스 (axiosClient가 자동으로 인증 및 토큰 갱신 처리)
// ==========================================

export const profileService = {
  // 마스터 데이터 조회
  async getAllergyMaster(): Promise<AllergyMaster[]> {
    const res = await api.get('/profile/master/allergies')
    return res.data
  },

  async getDislikeMaster(): Promise<DislikeMaster[]> {
    const res = await api.get('/profile/master/dislikes')
    return res.data
  },

  // 사용자 프로필 조회
  async getProfile(userId: string): Promise<UserProfile> {
    const res = await api.get(`/profile/${userId}`)
    return res.data
  },

  // 사용자 프로필 업데이트
  async updateProfile(userId: string, profile: UserProfileUpdate): Promise<UserProfile> {
    const res = await api.put(`/profile/${userId}`, profile)
    return res.data
  },

  // 알레르기 관리
  async addAllergy(userId: string, allergyId: number): Promise<void> {
    await api.post(`/profile/${userId}/allergies/${allergyId}`, {})
  },

  async removeAllergy(userId: string, allergyId: number): Promise<void> {
    await api.delete(`/profile/${userId}/allergies/${allergyId}`)
  },

  // 비선호 재료 관리
  async addDislike(userId: string, dislikeId: number): Promise<void> {
    await api.post(`/profile/${userId}/dislikes/${dislikeId}`, {})
  },

  async removeDislike(userId: string, dislikeId: number): Promise<void> {
    await api.delete(`/profile/${userId}/dislikes/${dislikeId}`)
  }
}

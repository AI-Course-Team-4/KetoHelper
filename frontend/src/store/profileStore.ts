import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { 
  profileService,
  UserProfile,
  UserProfileUpdate,
  AllergyMaster,
  DislikeMaster
} from '@/lib/profileService'

interface ProfileState {
  // 데이터
  profile: UserProfile | null
  allergyMaster: AllergyMaster[]
  dislikeMaster: DislikeMaster[]
  
  // 현재 로드된 프로필의 사용자 ID (캐시 무효화용)
  currentUserId: string | null
  
  // 상태
  isLoading: boolean
  error: string | null
  
  // 마스터 데이터 로드
  loadMasterData: () => Promise<void>
  
  // 프로필 관리
  loadProfile: (userId: string) => Promise<void>
  updateProfile: (userId: string, updates: UserProfileUpdate) => Promise<void>
  clearProfile: () => void
  
  // 알레르기 관리
  addAllergy: (userId: string, allergyId: number) => Promise<void>
  removeAllergy: (userId: string, allergyId: number) => Promise<void>
  
  // 비선호 재료 관리
  addDislike: (userId: string, dislikeId: number) => Promise<void>
  removeDislike: (userId: string, dislikeId: number) => Promise<void>
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set, get) => ({
      // 초기 상태
      profile: null,
      allergyMaster: [],
      dislikeMaster: [],
      currentUserId: null,
      isLoading: false,
      error: null,
      
      // 마스터 데이터 로드
      loadMasterData: async () => {
        set({ isLoading: true, error: null })
        try {
          const [allergies, dislikes] = await Promise.all([
            profileService.getAllergyMaster(),
            profileService.getDislikeMaster()
          ])
          
          set({ 
            allergyMaster: allergies,
            dislikeMaster: dislikes,
            isLoading: false 
          })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '마스터 데이터 로드 실패',
            isLoading: false 
          })
        }
      },
      
      // 프로필 로드
      loadProfile: async (userId) => {
        // 다른 사용자의 캐시된 데이터가 있으면 먼저 클리어
        const currentState = get()
        if (currentState.currentUserId && currentState.currentUserId !== userId) {
          set({ profile: null, currentUserId: null })
        }
        
        set({ isLoading: true, error: null })
        try {
          const profile = await profileService.getProfile(userId)
          set({ profile, currentUserId: userId, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '프로필 로드 실패',
            isLoading: false 
          })
        }
      },
      
      // 프로필 업데이트
      updateProfile: async (userId, updates) => {
        set({ isLoading: true, error: null })
        try {
          // 변경된 필드만 포함하는 payload 생성
          const payload: UserProfileUpdate = {}
          
          // 각 필드가 명시적으로 전달된 경우에만 포함
          if (updates.nickname !== undefined) {
            payload.nickname = updates.nickname
          }
          if (updates.goals_kcal !== undefined) {
            payload.goals_kcal = updates.goals_kcal
          }
          if (updates.goals_carbs_g !== undefined) {
            payload.goals_carbs_g = updates.goals_carbs_g
          }
          if (updates.selected_allergy_ids !== undefined) {
            payload.selected_allergy_ids = updates.selected_allergy_ids
          }
          if (updates.selected_dislike_ids !== undefined) {
            payload.selected_dislike_ids = updates.selected_dislike_ids
          }
          
          console.log('🔍 ProfileStore: 변경된 필드만 전송:', payload)
          
          // 현재 프로필을 미리 저장
          const currentProfile = get().profile
          
          const updatedProfile = await profileService.updateProfile(userId, payload)
          
          // 현재 프로필을 기반으로 업데이트된 필드만 변경
          const mergedProfile = {
            ...currentProfile,
            // 업데이트된 필드만 서버 응답으로 덮어쓰기
            ...(payload.nickname !== undefined && { nickname: updatedProfile.nickname }),
            ...(payload.goals_kcal !== undefined && { goals_kcal: updatedProfile.goals_kcal }),
            ...(payload.goals_carbs_g !== undefined && { goals_carbs_g: updatedProfile.goals_carbs_g }),
            ...(payload.selected_allergy_ids !== undefined && { selected_allergy_ids: updatedProfile.selected_allergy_ids }),
            ...(payload.selected_dislike_ids !== undefined && { selected_dislike_ids: updatedProfile.selected_dislike_ids }),
          } as UserProfile
          
          console.log('🔍 ProfileStore: 로컬 상태만 업데이트:', mergedProfile)
          set({ profile: mergedProfile, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '프로필 업데이트 실패',
            isLoading: false 
          })
          // 상위에서 실패를 감지할 수 있도록 에러 재발행
          throw (error instanceof Error ? error : new Error('프로필 업데이트 실패'))
        }
      },
      
      // 프로필 클리어
      clearProfile: () => {
        set({ profile: null, currentUserId: null, error: null })
      },
      
      // 알레르기 추가
      addAllergy: async (userId, allergyId) => {
        set({ isLoading: true, error: null })
        try {
          await profileService.addAllergy(userId, allergyId)
          
          // 프로필 다시 로드
          const updatedProfile = await profileService.getProfile(userId)
          set({ profile: updatedProfile, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '알레르기 추가 실패',
            isLoading: false 
          })
        }
      },
      
      // 알레르기 제거
      removeAllergy: async (userId, allergyId) => {
        set({ isLoading: true, error: null })
        try {
          await profileService.removeAllergy(userId, allergyId)
          
          // 프로필 다시 로드
          const updatedProfile = await profileService.getProfile(userId)
          set({ profile: updatedProfile, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '알레르기 제거 실패',
            isLoading: false 
          })
        }
      },
      
      // 비선호 재료 추가
      addDislike: async (userId, dislikeId) => {
        set({ isLoading: true, error: null })
        try {
          await profileService.addDislike(userId, dislikeId)
          
          // 프로필 다시 로드
          const updatedProfile = await profileService.getProfile(userId)
          set({ profile: updatedProfile, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '비선호 재료 추가 실패',
            isLoading: false 
          })
        }
      },
      
      // 비선호 재료 제거
      removeDislike: async (userId, dislikeId) => {
        set({ isLoading: true, error: null })
        try {
          await profileService.removeDislike(userId, dislikeId)
          
          // 프로필 다시 로드
          const updatedProfile = await profileService.getProfile(userId)
          set({ profile: updatedProfile, isLoading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '비선호 재료 제거 실패',
            isLoading: false 
          })
        }
      }
    }),
    {
      name: 'keto-coach-profile',
      partialize: (state) => ({ 
        profile: state.profile,
        currentUserId: state.currentUserId,
        allergyMaster: state.allergyMaster,
        dislikeMaster: state.dislikeMaster
      })
    }
  )
)

// 헬퍼 함수들
export const useProfileHelpers = () => {
  const store = useProfileStore()
  
  return {
    // 선택된 알레르기 이름들 가져오기
    getSelectedAllergyNames: (): string[] => {
      if (!store.profile || !store.allergyMaster.length) return []
      
      return store.allergyMaster
        .filter(allergy => store.profile!.selected_allergy_ids.includes(allergy.id))
        .map(allergy => allergy.name)
    },
    
    // 선택된 비선호 재료 이름들 가져오기
    getSelectedDislikeNames: (): string[] => {
      if (!store.profile || !store.dislikeMaster.length) return []
      
      return store.dislikeMaster
        .filter(dislike => store.profile!.selected_dislike_ids.includes(dislike.id))
        .map(dislike => dislike.name)
    },
    
    // 카테고리별 알레르기 그룹핑
    getAllergiesByCategory: (): Record<string, AllergyMaster[]> => {
      return store.allergyMaster.reduce((acc, allergy) => {
        const category = allergy.category || '기타'
        if (!acc[category]) acc[category] = []
        acc[category].push(allergy)
        return acc
      }, {} as Record<string, AllergyMaster[]>)
    },
    
    // 카테고리별 비선호 재료 그룹핑
    getDislikesByCategory: (): Record<string, DislikeMaster[]> => {
      return store.dislikeMaster.reduce((acc, dislike) => {
        const category = dislike.category || '기타'
        if (!acc[category]) acc[category] = []
        acc[category].push(dislike)
        return acc
      }, {} as Record<string, DislikeMaster[]>)
    }
  }
}
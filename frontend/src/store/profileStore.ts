import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface UserProfile {
  nickname?: string
  goals_kcal?: number
  goals_carbs_g?: number
  allergies: string[]
  dislikes: string[]
}

interface ProfileState {
  profile: UserProfile | null
  
  // Actions
  setProfile: (profile: UserProfile) => void
  updateProfile: (updates: Partial<UserProfile>) => void
  clearProfile: () => void
  addAllergy: (allergy: string) => void
  removeAllergy: (allergy: string) => void
  addDislike: (dislike: string) => void
  removeDislike: (dislike: string) => void
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set) => ({
      profile: null,
      
      setProfile: (profile) => {
        set({ profile })
      },
      
      updateProfile: (updates) => {
        set((state) => ({
          profile: state.profile ? { ...state.profile, ...updates } : updates as UserProfile
        }))
      },
      
      clearProfile: () => {
        set({ profile: null })
      },
      
      addAllergy: (allergy) => {
        set((state) => {
          if (!state.profile) return state
          
          const allergies = [...state.profile.allergies]
          if (!allergies.includes(allergy)) {
            allergies.push(allergy)
          }
          
          return {
            profile: { ...state.profile, allergies }
          }
        })
      },
      
      removeAllergy: (allergy) => {
        set((state) => {
          if (!state.profile) return state
          
          return {
            profile: {
              ...state.profile,
              allergies: state.profile.allergies.filter(a => a !== allergy)
            }
          }
        })
      },
      
      addDislike: (dislike) => {
        set((state) => {
          if (!state.profile) return state
          
          const dislikes = [...state.profile.dislikes]
          if (!dislikes.includes(dislike)) {
            dislikes.push(dislike)
          }
          
          return {
            profile: { ...state.profile, dislikes }
          }
        })
      },
      
      removeDislike: (dislike) => {
        set((state) => {
          if (!state.profile) return state
          
          return {
            profile: {
              ...state.profile,
              dislikes: state.profile.dislikes.filter(d => d !== dislike)
            }
          }
        })
      }
    }),
    {
      name: 'keto-coach-profile'
    }
  )
)

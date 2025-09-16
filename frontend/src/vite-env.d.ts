/// <reference types="vite/client" />

interface ImportMetaEnv {
<<<<<<< HEAD
    readonly VITE_SUPABASE_URL: string
    readonly VITE_SUPABASE_ANON_KEY: string
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv
  }
  
=======
  readonly VITE_API_BASE_URL: string
  readonly VITE_GOOGLE_CLIENT_ID: string
  readonly VITE_DEV_MODE?: string
  readonly VITE_LOG_LEVEL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  kakao: any;
}
>>>>>>> origin/dev

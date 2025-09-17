<<<<<<< HEAD
/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_SUPABASE_URL: string
    readonly VITE_SUPABASE_ANON_KEY: string
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv
  }
=======
/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_SUPABASE_URL: string
    readonly VITE_SUPABASE_ANON_KEY: string
    readonly VITE_KAKAO_MAP_JSKEY: string
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv
  }
>>>>>>> de7aaf3f92b9eaeb241486c6d211bba219ec20ec
  
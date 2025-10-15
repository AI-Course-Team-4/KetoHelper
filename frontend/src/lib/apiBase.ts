// 공통 API 베이스 URL (배포 HTTPS 보장, 로컬 폴백)
const RAW: string = ((import.meta as any).env?.VITE_API_BASE_URL || '').trim();

const trim = (s: string) => s.replace(/\/+$/, '');

const forceHttps = (u: string) =>
  typeof window !== 'undefined' && location.protocol === 'https:' && u.startsWith('http://')
    ? u.replace(/^http:\/\//, 'https://')
    : u;

export const API_BASE_URL: string = (() => {
  if (RAW) return `${trim(forceHttps(RAW))}/api/v1`;
  if (typeof window !== 'undefined' && location.protocol === 'https:') {
    // vercel 배포에서 환경변수가 비어있다면 Railway HTTPS로 강제 우회
    const host = location.hostname || ''
    if (/vercel\.app$/.test(host)) {
      return 'https://ketohelper-production.up.railway.app/api/v1'
    }
    return '/api/v1'
  }
  const local = ((import.meta as any).env?.VITE_LOCAL_BACKEND || 'http://localhost:8000').trim();
  return `${trim(local)}/api/v1`;
})();

export default API_BASE_URL;

// 공통 API 베이스 URL (배포 HTTPS 보장, 로컬 폴백)
const RAW: string = ((import.meta as any).env?.VITE_API_BASE_URL || '').trim();

const trim = (s: string) => s.replace(/\/+$/, '');

const forceHttps = (u: string) =>
  typeof window !== 'undefined' && location.protocol === 'https:' && u.startsWith('http://')
    ? u.replace(/^http:\/\//, 'https://')
    : u;

export const API_BASE_URL: string = (() => {
  if (RAW) return `${trim(forceHttps(RAW))}/api/v1`;
  if (typeof window !== 'undefined' && location.protocol === 'https:') return '/api/v1';
  const local = ((import.meta as any).env?.VITE_LOCAL_BACKEND || 'http://localhost:8000').trim();
  return `${trim(local)}/api/v1`;
})();

export default API_BASE_URL;

// 공통 API 베이스 URL 결정 유틸
// - 배포(https): 상대경로 사용해 vercel rewrites 타도록 보장 → Mixed Content 방지
// - 로컬: 환경변수 없으면 localhost로 폴백

const RAW: string = ((import.meta as any).env?.VITE_API_BASE_URL || '').trim();

const trimTrailingSlash = (s: string) => s.replace(/\/+$/, '');

const forceHttpsIfNeeded = (url: string) => {
  if (typeof window !== 'undefined' && location.protocol === 'https:' && url.startsWith('http://')) {
    return url.replace(/^http:\/\//, 'https://');
  }
  return url;
};

export const API_BASE_URL: string = (() => {
  // 1) 환경변수로 명시된 경우 우선 사용
  if (RAW) {
    const normalized = trimTrailingSlash(forceHttpsIfNeeded(RAW));
    // 프로젝트는 모든 API가 /api/v1 아래로 노출되므로 보장
    return `${normalized}/api/v1`;
  }

  // 2) 환경변수 미설정: 배포(https)에서는 상대경로로 rewrite 이용
  if (typeof window !== 'undefined' && location.protocol === 'https:') {
    return '/api/v1';
  }

  // 3) 로컬 개발 기본값
  const local = ((import.meta as any).env?.VITE_LOCAL_BACKEND || 'http://localhost:8000').trim();
  return `${trimTrailingSlash(local)}/api/v1`;
})();

export default API_BASE_URL;



// Google OAuth 로그인 서비스
declare global {
  interface Window {
    google: any;
    gapi: any;
  }
}

export interface GoogleUser {
  id: string;
  name: string;
  email: string;
  picture: string;
}

export interface GoogleSignInResult {
  user: GoogleUser;
  idToken: string;
}

class GoogleAuthService {
  private clientId: string;
  private isInitialized = false;

  constructor() {
    this.clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  }

  // Google API 초기화
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    return new Promise((resolve, reject) => {
      // Google API 스크립트 로드
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (window.google) {
          this.isInitialized = true;
          resolve();
        } else {
          reject(new Error('Google API 로드 실패'));
        }
      };
      script.onerror = () => reject(new Error('Google API 스크립트 로드 실패'));
      document.head.appendChild(script);
    });
  }

  // Google 로그인 (ID 토큰 + 사용자 정보 반환)
  async signIn(): Promise<GoogleSignInResult> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    if (!this.clientId) {
      throw new Error('Google Client ID가 설정되지 않았습니다.');
    }

    return new Promise((resolve, reject) => {
      try {
        // Google Identity Services 사용
        window.google.accounts.id.initialize({
          client_id: this.clientId,
          callback: (response: any) => {
            try {
              const idToken: string = response.credential;
              // JWT 토큰 디코딩
              const payload = this.parseJwt(idToken);
              const user: GoogleUser = {
                id: payload.sub,
                name: payload.name,
                email: payload.email,
                picture: payload.picture,
              };
              resolve({ user, idToken });
            } catch (error) {
              reject(error);
            }
          },
        });

        // 원탭 로그인 표시
        window.google.accounts.id.prompt();
        
        // 또는 버튼 클릭 시 팝업 로그인
        const btn = document.getElementById('google-signin-button');
        if (btn) {
          window.google.accounts.id.renderButton(btn, {
            theme: 'outline',
            size: 'large',
            width: '100%',
          });
        }
      } catch (error) {
        reject(error);
      }
    });
  }

  // 팝업으로 로그인 (대안 방법)
  async signInWithPopup(): Promise<GoogleUser> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      const popup = window.open(
        `https://accounts.google.com/oauth/authorize?client_id=${this.clientId}&redirect_uri=${window.location.origin}/auth/callback&response_type=code&scope=email profile`,
        'google-login',
        'width=500,height=600'
      );

      if (!popup) {
        reject(new Error('팝업이 차단되었습니다.'));
        return;
      }

      // 팝업에서 인증 완료 대기
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          reject(new Error('로그인이 취소되었습니다.'));
        }
      }, 1000);

      // PostMessage로 결과 받기
      window.addEventListener('message', (event) => {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'GOOGLE_AUTH_SUCCESS') {
          clearInterval(checkClosed);
          popup.close();
          resolve(event.data.user);
        } else if (event.data.type === 'GOOGLE_AUTH_ERROR') {
          clearInterval(checkClosed);
          popup.close();
          reject(new Error(event.data.error));
        }
      });
    });
  }

  // JWT 토큰 파싱
  private parseJwt(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      throw new Error('JWT 토큰 파싱 실패');
    }
  }

  // 로그아웃
  signOut(): void {
    if (window.google && window.google.accounts) {
      window.google.accounts.id.disableAutoSelect();
    }
  }
}

export const googleAuthService = new GoogleAuthService();

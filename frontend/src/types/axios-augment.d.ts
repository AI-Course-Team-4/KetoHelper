// Axios 타입 보강: 인터셉터에서 사용하는 커스텀 플래그를 정식 타입으로 확장
import 'axios'

declare module 'axios' {
  interface AxiosRequestConfig {
    _retry?: boolean
  }

  interface AxiosError<T = any, D = any> {
    _isHandled?: boolean
    _suppressToast?: boolean
  }
}



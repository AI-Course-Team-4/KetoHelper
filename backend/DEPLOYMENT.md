# 배포 환경 설정 가이드

## 환경 변수 설정

### 개발 환경 (.env)
```bash
ENVIRONMENT=development
COOKIE_DOMAIN=localhost
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

### 프로덕션 환경
```bash
ENVIRONMENT=production
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

## 쿠키 설정 설명

### COOKIE_DOMAIN
- **개발**: `localhost` (명시적 설정)
- **프로덕션**: `yourdomain.com` 또는 `None` (자동 설정)

### COOKIE_SECURE
- **개발**: `false` (HTTP 허용)
- **프로덕션**: `true` (HTTPS만 허용)

### COOKIE_SAMESITE
- **권장**: `lax` (CSRF 보호 + 사용성)
- **엄격**: `strict` (최고 보안)
- **비활성**: `none` (secure=true 필요)

## 배포 플랫폼별 설정

### Vercel
```bash
ENVIRONMENT=production
COOKIE_DOMAIN=your-app.vercel.app
COOKIE_SECURE=true
```

### Netlify
```bash
ENVIRONMENT=production
COOKIE_DOMAIN=your-app.netlify.app
COOKIE_SECURE=true
```

### AWS/EC2
```bash
ENVIRONMENT=production
COOKIE_DOMAIN=yourdomain.com
COOKIE_SECURE=true
```

## 보안 체크리스트

- [ ] HTTPS 사용 (프로덕션)
- [ ] COOKIE_SECURE=true (프로덕션)
- [ ] 적절한 도메인 설정
- [ ] SAMESITE 설정 검토
- [ ] JWT 시크릿 키 보안
- [ ] 환경 변수 암호화

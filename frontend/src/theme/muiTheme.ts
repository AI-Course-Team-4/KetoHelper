import { createTheme } from '@mui/material/styles';

// MUI 테마 설정 - Tailwind CSS를 완전 대체하도록 구성
export const muiTheme = createTheme({
  palette: {
    primary: {
      main: 'hsl(142, 76%, 36%)', // CSS 변수와 동일한 값
      light: 'hsl(142, 76%, 46%)', // 더 밝은 버전
      dark: 'hsl(142, 76%, 26%)', // 더 어두운 버전
      50: 'hsl(142, 76%, 95%)', // 매우 연한 초록색
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#6b7280', // gray-500
      light: '#9ca3af', // gray-400
      dark: '#374151', // gray-700
      contrastText: '#ffffff',
    },
    error: {
      main: '#ef4444', // red-500
      light: '#f87171', // red-400
      dark: '#dc2626', // red-600
    },
    warning: {
      main: '#f59e0b', // amber-500
      light: '#fbbf24', // amber-400
      dark: '#d97706', // amber-600
    },
    success: {
      main: '#22c55e', // green-500
      light: '#4ade80', // green-400
      dark: '#16a34a', // green-600
    },
    info: {
      main: '#06b6d4', // cyan-500
      light: '#22d3ee', // cyan-400
      dark: '#0891b2', // cyan-600
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
    text: {
      primary: '#111827', // gray-900
      secondary: '#6b7280', // gray-500
    },
    // Tailwind의 추가 색상들
    grey: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.25rem', // text-4xl
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '1.875rem', // text-3xl
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem', // text-2xl
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem', // text-xl
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem', // text-lg
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem', // text-base
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem', // text-base
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem', // text-sm
      lineHeight: 1.5,
    },
    button: {
      fontSize: '0.875rem', // text-sm
      fontWeight: 500,
      textTransform: 'none', // MUI 기본값인 대문자 변환 비활성화
    },
  },
  shape: {
    borderRadius: 8, // rounded-lg
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '0.5rem', // rounded-lg
          textTransform: 'none',
          fontWeight: 500,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          backgroundColor: 'primary.main',
          color: 'primary.contrastText',
          '&:hover': {
            backgroundColor: 'primary.dark',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
        },
        outlined: {
          borderColor: 'primary.main',
          color: 'primary.main',
          '&:hover': {
            backgroundColor: 'primary.main',
            color: 'primary.contrastText',
            borderColor: 'primary.main',
          },
        },
      },
    },
    MuiStack: {
      styleOverrides: {
        root: {
          // 기본 Stack 스타일링
        },
      },
    },
    MuiTypography: {
      styleOverrides: {
        root: {
          // 기본 Typography 스타일링
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: '0.75rem', // rounded-xl
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '0.5rem', // rounded-lg
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: '0.5rem', // rounded-lg
        },
      },
    },
            MuiAutocomplete: {
              styleOverrides: {
                root: {
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '0.5rem', // rounded-lg
                  },
                },
              },
            },
            MuiChip: {
              styleOverrides: {
                root: {
                  borderRadius: '1rem', // rounded-full
                },
              },
            },
            MuiCard: {
              styleOverrides: {
                root: {
                  boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)', // 아주 미세한 그림자
                  border: '1px solid #e5e7eb', // gray-200 테두리
                  '&:hover': {
                    boxShadow: '0 2px 4px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)', // 호버 시 조금 더 강한 그림자
                  },
                },
              },
            },
            MuiCardHeader: {
              styleOverrides: {
                root: {
                  padding: '16px 24px', // 기본 패딩 유지
                  '& .MuiCardHeader-title': {
                    fontSize: '1.125rem', // text-lg
                    fontWeight: 600,
                    lineHeight: 1.4,
                  },
                },
              },
            },
  },
});

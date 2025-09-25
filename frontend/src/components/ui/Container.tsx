import React from 'react';
import { Box, BoxProps } from '@mui/material';

// Tailwind의 container 클래스를 MUI로 대체
export interface ContainerProps extends Omit<BoxProps, 'maxWidth'> {
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  center?: boolean;
}

export const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ maxWidth = 'lg', center = true, sx, ...props }, ref) => {
    return (
      <Box
        ref={ref}
        sx={{
          width: '100%',
          maxWidth: maxWidth === false ? 'none' : {
            xs: '100%',
            sm: '640px',
            md: '768px',
            lg: '1024px',
            xl: '1280px',
          }[maxWidth],
          mx: center ? 'auto' : 0,
          px: { xs: 2, sm: 3, md: 4 },
          ...sx,
        }}
        {...props}
      />
    );
  }
);

Container.displayName = 'Container';

import React from 'react';
import { Box, BoxProps } from '@mui/material';

// Tailwind의 space-y, gap 등을 MUI로 대체
export interface SpacerProps extends BoxProps {
  size?: number | string;
  direction?: 'vertical' | 'horizontal';
}

export const Spacer = React.forwardRef<HTMLDivElement, SpacerProps>(
  ({ size = 1, direction = 'vertical', sx, ...props }, ref) => {
    return (
      <Box
        ref={ref}
        sx={{
          ...(direction === 'vertical' 
            ? { height: size, width: '100%' }
            : { width: size, height: '100%' }
          ),
          ...sx,
        }}
        {...props}
      />
    );
  }
);

Spacer.displayName = 'Spacer';

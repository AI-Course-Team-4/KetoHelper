import React from 'react';
import { Grid as MuiGrid, GridProps as MuiGridProps } from '@mui/material';

// Tailwind의 grid 시스템을 MUI로 대체
export interface GridProps extends Omit<MuiGridProps, 'container' | 'item'> {
  container?: boolean;
  item?: boolean;
  cols?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
  gap?: number | string;
}

export const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ cols, gap = 2, sx, ...props }, ref) => {
    const gridProps: MuiGridProps = {
      ...props,
      sx: {
        ...(cols && typeof cols === 'number' && {
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
        }),
        ...(cols && typeof cols === 'object' && {
          gridTemplateColumns: {
            xs: cols.xs ? `repeat(${cols.xs}, 1fr)` : '1fr',
            sm: cols.sm ? `repeat(${cols.sm}, 1fr)` : '1fr',
            md: cols.md ? `repeat(${cols.md}, 1fr)` : '1fr',
            lg: cols.lg ? `repeat(${cols.lg}, 1fr)` : '1fr',
            xl: cols.xl ? `repeat(${cols.xl}, 1fr)` : '1fr',
          },
        }),
        gap,
        ...sx,
      },
    };

    return <MuiGrid ref={ref} {...gridProps} />;
  }
);

Grid.displayName = 'Grid';

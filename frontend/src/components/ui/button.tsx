import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps, CircularProgress } from '@mui/material';

export interface ButtonProps extends Omit<MuiButtonProps, 'variant' | 'size'> {
  variant?: 'contained' | 'outlined' | 'text' | 'default' | 'ghost' | 'destructive' | 'secondary' | 'link' | 'outline';
  size?: 'small' | 'medium' | 'large' | 'sm' | 'lg' | 'default' | 'icon';
  loading?: boolean;
  loadingText?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ loading = false, loadingText, children, disabled, variant, size, ...props }, ref) => {
    // variant 매핑
    const muiVariant = variant === 'default' ? 'contained' : 
                      variant === 'ghost' ? 'text' :
                      variant === 'outline' ? 'outlined' :
                      variant === 'destructive' ? 'contained' :
                      variant === 'secondary' ? 'outlined' :
                      variant === 'link' ? 'text' :
                      variant || 'contained';

    // size 매핑
    const muiSize = size === 'sm' ? 'small' :
                   size === 'lg' ? 'large' :
                   size === 'default' ? 'medium' :
                   size === 'icon' ? 'small' :
                   size || 'medium';

    return (
      <MuiButton
        ref={ref}
        disabled={disabled || loading}
        variant={muiVariant}
        size={muiSize}
        startIcon={loading ? <CircularProgress size={16} /> : props.startIcon}
        {...props}
      >
        {loading && loadingText ? loadingText : children}
      </MuiButton>
    );
  }
);

Button.displayName = 'Button';
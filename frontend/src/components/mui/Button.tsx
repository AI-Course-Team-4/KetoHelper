import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps, CircularProgress } from '@mui/material';

export interface ButtonProps extends Omit<MuiButtonProps, 'variant'> {
  variant?: 'contained' | 'outlined' | 'text' | 'contained' | 'outlined' | 'text';
  loading?: boolean;
  loadingText?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ loading = false, loadingText, children, disabled, ...props }, ref) => {
    return (
      <MuiButton
        ref={ref}
        disabled={disabled || loading}
        startIcon={loading ? <CircularProgress size={16} /> : props.startIcon}
        {...props}
      >
        {loading && loadingText ? loadingText : children}
      </MuiButton>
    );
  }
);

Button.displayName = 'Button';

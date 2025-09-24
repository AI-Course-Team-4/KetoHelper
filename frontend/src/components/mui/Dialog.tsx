import React from 'react';
import {
  Dialog as MuiDialog,
  DialogProps as MuiDialogProps,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  IconButton,
  Box,
} from '@mui/material';
import { Close } from '@mui/icons-material';

export interface DialogProps extends Omit<MuiDialogProps, 'open'> {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  showCloseButton?: boolean;
  actions?: React.ReactNode;
}

export const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
  ({ 
    open, 
    onClose, 
    title, 
    description, 
    showCloseButton = true, 
    actions, 
    children, 
    ...props 
  }, ref) => {
    return (
      <MuiDialog
        ref={ref}
        open={open}
        onClose={onClose}
        maxWidth="sm"
        fullWidth
        {...props}
      >
        {(title || showCloseButton) && (
          <DialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              {title}
              {showCloseButton && (
                <IconButton
                  aria-label="close"
                  onClick={onClose}
                  sx={{ ml: 1 }}
                >
                  <Close />
                </IconButton>
              )}
            </Box>
          </DialogTitle>
        )}
        
        <DialogContent>
          {description && (
            <DialogContentText sx={{ mb: 2 }}>
              {description}
            </DialogContentText>
          )}
          {children}
        </DialogContent>
        
        {actions && (
          <DialogActions>
            {actions}
          </DialogActions>
        )}
      </MuiDialog>
    );
  }
);

Dialog.displayName = 'Dialog';

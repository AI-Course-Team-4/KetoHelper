import React from 'react';
import {
  Dialog as MuiDialog,
  DialogProps as MuiDialogProps,
  DialogTitle as MuiDialogTitle,
  DialogContent as MuiDialogContent,
  DialogActions,
  DialogContentText,
  IconButton,
  Box,
} from '@mui/material';
import { Close } from '@mui/icons-material';

export interface DialogProps extends Omit<MuiDialogProps, 'open'> {
  open: boolean;
  onClose: () => void;
  onOpenChange?: (open: boolean) => void;
  title?: string;
  description?: string;
  showCloseButton?: boolean;
  actions?: React.ReactNode;
}

export const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
  ({ 
    open, 
    onClose, 
    onOpenChange,
    title, 
    description, 
    showCloseButton = true, 
    actions, 
    children, 
    ...props 
  }, ref) => {
    const handleClose = () => {
      onClose();
      onOpenChange?.(false);
    };
    return (
      <MuiDialog
        ref={ref}
        open={open}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        {...props}
      >
        {(title || showCloseButton) && (
          <MuiDialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              {title}
              {showCloseButton && (
                <IconButton
                  aria-label="close"
                  onClick={handleClose}
                  sx={{ ml: 1 }}
                >
                  <Close />
                </IconButton>
              )}
            </Box>
          </MuiDialogTitle>
        )}
        
        <MuiDialogContent>
          {description && (
            <DialogContentText sx={{ mb: 2 }}>
              {description}
            </DialogContentText>
          )}
          {children}
        </MuiDialogContent>
        
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

// 기존 API와의 호환성을 위한 별칭들
export const DialogContent = MuiDialogContent;
export const DialogHeader = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <Box {...props}>{children}</Box>
);
export const DialogFooter = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <Box {...props}>{children}</Box>
);
export const DialogTitle = MuiDialogTitle;
export const DialogDescription = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <Box {...props}>{children}</Box>
);
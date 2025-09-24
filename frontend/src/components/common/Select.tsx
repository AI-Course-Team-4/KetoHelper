import React from 'react';
import {
  Select as MuiSelect,
  SelectProps as MuiSelectProps,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
} from '@mui/material';

export interface SelectProps extends Omit<MuiSelectProps, 'value' | 'onChange'> {
  value?: string;
  onChange?: (value: string) => void;
  options?: Array<{ value: string; label: string; disabled?: boolean }>;
  placeholder?: string;
  error?: boolean;
  helperText?: string;
  label?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ 
    value, 
    onChange, 
    options = [], 
    placeholder, 
    error, 
    helperText, 
    label,
    ...props 
  }, ref) => {
    return (
      <FormControl fullWidth error={error}>
        {label && <InputLabel>{label}</InputLabel>}
        <MuiSelect
          ref={ref}
          value={value || ''}
          onChange={(e) => onChange?.(e.target.value as string)}
          displayEmpty
          {...props}
        >
          {placeholder && (
            <MenuItem value="" disabled>
              {placeholder}
            </MenuItem>
          )}
          {options.map((option) => (
            <MenuItem 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </MenuItem>
          ))}
        </MuiSelect>
        {helperText && <FormHelperText>{helperText}</FormHelperText>}
      </FormControl>
    );
  }
);

Select.displayName = 'Select';

// 기존 API와의 호환성을 위한 별칭들
export const SelectTrigger = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectContent = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectItem = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectValue = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectGroup = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectLabel = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectSeparator = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectScrollUpButton = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);
export const SelectScrollDownButton = ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props}>{children}</div>
);

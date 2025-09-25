import {
  Autocomplete as MuiAutocomplete,
  AutocompleteProps as MuiAutocompleteProps,
  TextField,
  Chip,
} from '@mui/material';

export interface AutocompleteProps<T> extends Omit<MuiAutocompleteProps<T, true, false, false>, 'renderInput'> {
  label?: string;
  placeholder?: string;
  error?: boolean;
  helperText?: string;
  chipColor?: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
}

export function Autocomplete<T extends string>({
  label,
  placeholder,
  error,
  helperText,
  chipColor = 'primary',
  ...props
}: AutocompleteProps<T>) {
  return (
    <MuiAutocomplete
      multiple
      renderTags={(value, getTagProps) =>
        value.map((option, index) => (
          <Chip
            {...getTagProps({ index })}
            key={index}
            label={String(option)}
            color={chipColor}
            size="small"
          />
        ))
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={placeholder}
          error={error}
          helperText={helperText}
          variant="outlined"
        />
      )}
      {...props}
    />
  );
}

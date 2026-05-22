import React from 'react';

/**
 * Reusable Form Input component with validation
 * @param {Object} props - Component props
 */
export function FormInput({
  name,
  label,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  touched,
  placeholder,
  required = false,
  disabled = false,
  autoComplete,
  ...props
}) {
  const hasError = error && touched;
  const inputId = `input-${name}`;

  return (
    <div className="form-group" style={{ marginBottom: '20px' }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            display: 'block',
            fontWeight: '500',
            marginBottom: '8px',
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
          }}
        >
          {label}
          {required && (
            <span style={{ color: 'var(--danger)', marginLeft: '4px' }}>*</span>
          )}
        </label>
      )}

      <input
        id={inputId}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete={autoComplete}
        aria-invalid={hasError}
        aria-describedby={hasError ? `${inputId}-error` : undefined}
        style={{
          width: '100%',
          padding: '10px 12px',
          backgroundColor: 'var(--surface-base)',
          border: `1px solid ${hasError ? 'var(--danger)' : 'var(--border-subtle)'}`,
          borderRadius: '8px',
          fontSize: '1rem',
          color: 'var(--text-primary)',
          outline: 'none',
          transition: 'all 0.2s',
          opacity: disabled ? '0.5' : '1',
          cursor: disabled ? 'not-allowed' : 'text',
          ...(hasError && {
            boxShadow: '0 0 0 3px rgba(218, 54, 51, 0.1)',
          }),
        }}
        {...props}
      />

      {hasError && (
        <div
          id={`${inputId}-error`}
          role="alert"
          style={{
            marginTop: '6px',
            fontSize: '0.875rem',
            color: 'var(--danger)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}

/**
 * Reusable Form Select component with validation
 */
export function FormSelect({
  name,
  label,
  value,
  onChange,
  onBlur,
  error,
  touched,
  options = [],
  placeholder = 'Select an option',
  required = false,
  disabled = false,
  ...props
}) {
  const hasError = error && touched;
  const selectId = `select-${name}`;

  return (
    <div className="form-group" style={{ marginBottom: '20px' }}>
      {label && (
        <label
          htmlFor={selectId}
          style={{
            display: 'block',
            fontWeight: '500',
            marginBottom: '8px',
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
          }}
        >
          {label}
          {required && (
            <span style={{ color: 'var(--danger)', marginLeft: '4px' }}>*</span>
          )}
        </label>
      )}

      <select
        id={selectId}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        aria-invalid={hasError}
        aria-describedby={hasError ? `${selectId}-error` : undefined}
        style={{
          width: '100%',
          padding: '10px 12px',
          backgroundColor: 'var(--surface-base)',
          border: `1px solid ${hasError ? 'var(--danger)' : 'var(--border-subtle)'}`,
          borderRadius: '8px',
          fontSize: '1rem',
          color: 'var(--text-primary)',
          outline: 'none',
          transition: 'all 0.2s',
          opacity: disabled ? '0.5' : '1',
          cursor: disabled ? 'not-allowed' : 'pointer',
          ...(hasError && {
            boxShadow: '0 0 0 3px rgba(218, 54, 51, 0.1)',
          }),
        }}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>

      {hasError && (
        <div
          id={`${selectId}-error`}
          role="alert"
          style={{
            marginTop: '6px',
            fontSize: '0.875rem',
            color: 'var(--danger)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}

/**
 * Reusable Form Checkbox component
 */
export function FormCheckbox({
  name,
  label,
  checked,
  onChange,
  onBlur,
  error,
  touched,
  disabled = false,
  required = false,
  ...props
}) {
  const hasError = error && touched;
  const checkboxId = `checkbox-${name}`;

  return (
    <div className="form-group" style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <input
          id={checkboxId}
          name={name}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${checkboxId}-error` : undefined}
          style={{
            width: '18px',
            height: '18px',
            marginTop: '2px',
            accentColor: 'var(--accent)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? '0.5' : '1',
          }}
          {...props}
        />

        <div style={{ flex: 1 }}>
          {label && (
            <label
              htmlFor={checkboxId}
              style={{
                display: 'block',
                fontWeight: '500',
                fontSize: '0.875rem',
                color: 'var(--text-primary)',
                cursor: disabled ? 'not-allowed' : 'pointer',
                lineHeight: '1.5',
              }}
            >
              {label}
              {required && (
                <span style={{ color: 'var(--danger)', marginLeft: '4px' }}>*</span>
              )}
            </label>
          )}

          {hasError && (
            <div
              id={`${checkboxId}-error`}
              role="alert"
              style={{
                marginTop: '6px',
                fontSize: '0.875rem',
                color: 'var(--danger)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Reusable Form Button component
 */
export function FormButton({
  type = 'submit',
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  children,
  onClick,
  ...props
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px 24px',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: 'none',
    outline: 'none',
  };

  const variants = {
    primary: {
      background: 'var(--accent)',
      color: '#fff',
      border: 'none',
    },
    secondary: {
      background: 'transparent',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-subtle)',
    },
    danger: {
      background: 'var(--danger)',
      color: '#fff',
      border: 'none',
    },
    success: {
      background: 'var(--success)',
      color: '#fff',
      border: 'none',
    },
  };

  const sizes = {
    small: {
      padding: '8px 16px',
      fontSize: '0.8125rem',
    },
    medium: {
      padding: '12px 24px',
      fontSize: '0.875rem',
    },
    large: {
      padding: '16px 32px',
      fontSize: '1rem',
    },
  };

  const variantStyles = variants[variant] || variants.primary;
  const sizeStyles = sizes[size] || sizes.medium;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        ...baseStyles,
        ...variantStyles,
        ...sizeStyles,
        opacity: disabled || loading ? '0.5' : '1',
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
      }}
      {...props}
    >
      {loading && (
        <svg
          className="spin"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      )}
      {children}
    </button>
  );
}
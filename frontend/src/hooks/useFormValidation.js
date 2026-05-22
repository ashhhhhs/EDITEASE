import { useState, useCallback } from 'react';

/**
 * Custom hook for form validation
 * @param {Object} initialValues - Initial form values
 * @param {Object} validationRules - Validation rules for each field
 * @returns {Object} Form state and handlers
 */
export function useFormValidation(initialValues = {}, validationRules = {}) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Validate a single field
   * @param {string} name - Field name
   * @param {string} value - Field value
   * @returns {string|null} Error message or null if valid
   */
  const validateField = useCallback((name, value) => {
    const rules = validationRules[name];
    if (!rules) return null;

    // Required validation
    if (rules.required && (!value || value.trim() === '')) {
      return rules.requiredMessage || `${name} is required`;
    }

    // Email validation
    if (rules.email && value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        return rules.emailMessage || 'Please enter a valid email address';
      }
    }

    // Min length validation
    if (rules.minLength && value && value.length < rules.minLength) {
      return rules.minLengthMessage || `${name} must be at least ${rules.minLength} characters`;
    }

    // Max length validation
    if (rules.maxLength && value && value.length > rules.maxLength) {
      return rules.maxLengthMessage || `${name} must not exceed ${rules.maxLength} characters`;
    }

    // Pattern validation
    if (rules.pattern && value && !rules.pattern.test(value)) {
      return rules.patternMessage || `${name} format is invalid`;
    }

    // Custom validation
    if (rules.validate && typeof rules.validate === 'function') {
      const customError = rules.validate(value, values);
      if (customError) {
        return customError;
      }
    }

    // Match validation (for password confirmation, etc.)
    if (rules.match && value !== values[rules.match]) {
      return rules.matchMessage || `${name} does not match`;
    }

    return null;
  }, [validationRules, values]);

  /**
   * Validate all fields
   * @returns {boolean} True if all fields are valid
   */
  const validateAll = useCallback(() => {
    const newErrors = {};
    let isValid = true;

    Object.keys(validationRules).forEach((name) => {
      const error = validateField(name, values[name]);
      if (error) {
        newErrors[name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [validationRules, values, validateField]);

  /**
   * Handle field change
   * @param {Event} e - Change event
   */
  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const fieldValue = type === 'checkbox' ? checked : value;

    setValues((prev) => ({
      ...prev,
      [name]: fieldValue,
    }));

    // Validate field if it has been touched
    if (touched[name]) {
      const error = validateField(name, fieldValue);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    }
  }, [touched, validateField]);

  /**
   * Handle field blur
   * @param {Event} e - Blur event
   */
  const handleBlur = useCallback((e) => {
    const { name } = e.target;

    setTouched((prev) => ({
      ...prev,
      [name]: true,
    }));

    const error = validateField(name, values[name]);
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  }, [values, validateField]);

  /**
   * Handle form submission
   * @param {Function} onSubmit - Submit callback
   */
  const handleSubmit = useCallback(async (onSubmit) => {
    // Mark all fields as touched
    setTouched(
      Object.keys(validationRules).reduce((acc, name) => ({ ...acc, [name]: true }), {})
    );

    // Validate all fields
    const isValid = validateAll();

    if (!isValid) {
      return false;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(values);
      return true;
    } catch (error) {
      console.error('Form submission error:', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [validationRules, values, validateAll]);

  /**
   * Reset form to initial values
   */
  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  /**
   * Set a specific field value
   * @param {string} name - Field name
   * @param {any} value - Field value
   */
  const setFieldValue = useCallback((name, value) => {
    setValues((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Validate field if it has been touched
    if (touched[name]) {
      const error = validateField(name, value);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    }
  }, [touched, validateField]);

  /**
   * Set a specific field error
   * @param {string} name - Field name
   * @param {string} error - Error message
   */
  const setFieldError = useCallback((name, error) => {
    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  }, []);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm,
    setFieldValue,
    setFieldError,
    validateField,
    validateAll,
    isValid: Object.keys(errors).length === 0,
  };
}

/**
 * Common validation rules
 */
export const validationRules = {
  required: (message) => ({
    required: true,
    requiredMessage: message,
  }),

  email: (message) => ({
    email: true,
    emailMessage: message || 'Please enter a valid email address',
  }),

  minLength: (length, message) => ({
    minLength: length,
    minLengthMessage: message || `Must be at least ${length} characters`,
  }),

  maxLength: (length, message) => ({
    maxLength: length,
    maxLengthMessage: message || `Must not exceed ${length} characters`,
  }),

  pattern: (regex, message) => ({
    pattern: regex,
    patternMessage: message,
  }),

  match: (fieldName, message) => ({
    match: fieldName,
    matchMessage: message || `Must match ${fieldName}`,
  }),

  custom: (validator) => ({
    validate: validator,
  }),
};
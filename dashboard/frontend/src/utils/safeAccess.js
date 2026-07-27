import { watch, computed } from 'vue';

/**
 * Safe access utilities for LingWen Dashboard
 * Provides safe property access, store access, and reactive utilities
 */

/**
 * Safely access nested object properties by dot-notation path
 * @param {object} obj - Target object
 * @param {string|Array<string>} path - Property path (e.g., 'a.b.c' or ['a', 'b', 'c'])
 * @param {*} defaultValue - Fallback value when path is not accessible
 * @returns {*} Value at path or defaultValue
 */
export function safeAccess(obj, path, defaultValue) {
  if (!obj) return defaultValue
  const keys = Array.isArray(path) ? path : path.split('.')
  return keys.reduce((current, key) => current?.[key], obj) ?? defaultValue
}

/**
 * Safely access Pinia store properties
 * @param {object} store - Pinia store instance
 * @param {string|Array<string>} path - Property path
 * @param {*} defaultValue - Fallback value
 * @returns {*} Value at path or defaultValue
 */
export function safeStore(store, path, defaultValue) {
  if (!store) return defaultValue
  return safeAccess(store, path, defaultValue)
}

/**
 * Safely unwrap a ref value
 * @param {import('vue').Ref<*>} refValue - Vue ref
 * @param {*} defaultValue - Fallback value
 * @returns {*} Unwrapped value or defaultValue
 */
export function safeRef(refValue, defaultValue) {
  if (refValue === null || refValue === undefined) return defaultValue
  return refValue.value ?? defaultValue
}

/**
 * Safe watch that skips null/undefined values
 * @param {import('vue').WatchSource} watchSource - Vue watch source
 * @param {import('vue').WatchCallback} callback - Watch callback
 * @param {import('vue').WatchOptions} [options] - Watch options
 * @returns {import('vue').StopHandle} Stop handle
 */
export function safeWatch(watchSource, callback, options) {
  return watch(watchSource, (newVal, oldVal) => {
    if (newVal === null || newVal === undefined) return
    callback(newVal, oldVal)
  }, options)
}

/**
 * Safe computed that catches errors and returns default value
 * @param {() => *} getter - Computed getter
 * @param {*} defaultValue - Fallback value
 * @returns {import('vue').ComputedRef<*>}
 */
export function safeComputed(getter, defaultValue) {
  return computed(() => {
    try {
      const result = getter()
      return result ?? defaultValue
    } catch {
      return defaultValue
    }
  })
}

/**
 * Return value with fallback to default
 * @param {*} value - Value to check
 * @param {*} defaultValue - Fallback value
 * @returns {*} Value or defaultValue
 */
export function withDefault(value, defaultValue) {
  return value ?? defaultValue
}

/**
 * Check if value is defined (not null or undefined)
 * @param {*} value - Value to check
 * @returns {boolean}
 */
export function isDefined(value) {
  return value !== null && value !== undefined
}
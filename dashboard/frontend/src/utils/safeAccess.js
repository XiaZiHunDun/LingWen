export function safeAccess(obj, path, defaultValue) {
  if (!obj) return defaultValue
  const keys = Array.isArray(path) ? path : path.split('.')
  return keys.reduce((current, key) => current?.[key], obj) ?? defaultValue
}

export function safeStore(store, path, defaultValue) {
  if (!store) return defaultValue
  return safeAccess(store, path, defaultValue)
}

export function safeRef(refValue, defaultValue) {
  if (refValue === null || refValue === undefined) return defaultValue
  return refValue.value ?? defaultValue
}

export function safeWatch(watchSource, callback, options) {
  return watch(watchSource, (newVal, oldVal) => {
    if (newVal === null || newVal === undefined) return
    callback(newVal, oldVal)
  }, options)
}

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

export function withDefault(value, defaultValue) {
  return value ?? defaultValue
}

export function isDefined(value) {
  return value !== null && value !== undefined
}
import { logger } from './logger.js';

export function createSafeStoreWrapper(useStore) {
  return function () {
    const store = useStore()
    if (!store) {
      return new Proxy({}, {
        get() {
          return safeValue
        },
        has() {
          return true
        },
      })
    }

    return new Proxy(store, {
      get(target, prop) {
        if (prop === 'then') return undefined
        if (prop === '__v_isRef') return target.__v_isRef

        const value = target[prop]

        if (typeof value === 'function') {
          return (...args) => {
            try {
              const result = value.apply(target, args)
              if (result instanceof Promise) {
                return result.catch(error => {
                  logger.error(`[safeStore] 调用 ${String(prop)} 失败:`, error)
                  return null
                })
              }
              return result
            } catch (error) {
              logger.error(`[safeStore] 调用 ${String(prop)} 失败:`, error)
              return null
            }
          }
        }

        if (value === null || value === undefined) {
          return safeValue
        }

        if (typeof value === 'object') {
          return new Proxy(value, {
            get(obj, key) {
              if (key === 'then') return undefined
              if (key === 'value' && obj.value !== undefined) {
                return obj.value ?? null
              }
              return obj[key] ?? safeValue
            },
            has() {
              return true
            },
          })
        }

        return value
      },
      has() {
        return true
      },
    })
  }
}

const safeValue = new Proxy({}, {
  get() {
    return safeValue
  },
  has() {
    return true
  },
  apply() {
    return safeValue
  },
})

export function safeCall(fn, ...args) {
  if (typeof fn !== 'function') return null
  try {
    return fn(...args)
  } catch (err) {
    logger.warn('[safeCall] function call failed:', err)
    return null
  }
}

export function safeAsyncCall(fn, ...args) {
  if (typeof fn !== 'function') return Promise.resolve(null)
  return fn(...args).catch(err => {
    logger.warn('[safeAsyncCall] async call failed:', err)
    return null
  })
}

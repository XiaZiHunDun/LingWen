import { ref, computed, onMounted, onUnmounted } from 'vue'

/**
 * 屏幕断点定义
 */
const breakpoints = {
  xs: 360,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  '2xl': 1400,
}

/**
 * 设备类型检测
 */
const deviceType = ref('desktop')
const screenWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1200)
const screenHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 800)
const isTouch = ref('ontouchstart' in window || navigator.maxTouchPoints > 0)
const isDesktopApp = ref(false)
const platform = ref('unknown')

/**
 * 更新设备类型
 */
function updateDeviceType() {
  const width = window.innerWidth
  screenWidth.value = width
  screenHeight.value = window.innerHeight

  if (width >= breakpoints.lg) {
    deviceType.value = 'desktop'
  } else if (width >= breakpoints.md) {
    deviceType.value = 'tablet'
  } else {
    deviceType.value = 'mobile'
  }

  // 更新 CSS 变量
  updateCssVariables()
}

/**
 * 更新 CSS 变量
 */
function updateCssVariables() {
  const root = document.documentElement
  
  root.style.setProperty('--device-type', deviceType.value)
  root.style.setProperty('--breakpoint', breakpoint.value)
  root.style.setProperty('--viewport-width', `${screenWidth.value}px`)
  root.style.setProperty('--viewport-height', `${screenHeight.value}px`)
  
  // 设置响应式字体大小
  const fontSize = Math.max(14, Math.min(16, screenWidth.value / 50))
  root.style.setProperty('--base-font-size', `${fontSize}px`)
  
  // 设置触摸设备指示器
  root.style.setProperty('--is-touch', isTouch.value ? 'true' : 'false')
}

/**
 * 检测桌面应用环境
 */
function detectDesktopApp() {
  // Tauri 环境检测
  if (window.__TAURI__) {
    isDesktopApp.value = true
    platform.value = 'tauri'
    return
  }
  
  // Electron 环境检测
  if (window.electronAPI || process?.type === 'renderer') {
    isDesktopApp.value = true
    platform.value = 'electron'
    return
  }
  
  // 检查 User Agent
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('electron') || ua.includes('tauri')) {
    isDesktopApp.value = true
    platform.value = ua.includes('electron') ? 'electron' : 'tauri'
    return
  }
  
  // 默认为浏览器
  platform.value = 'browser'
}

let resizeObserver = null

export function useDevice() {
  onMounted(() => {
    detectDesktopApp()
    updateDeviceType()
    window.addEventListener('resize', updateDeviceType, { passive: true })

    resizeObserver = new ResizeObserver(() => {
      updateDeviceType()
    })

    if (document.body) {
      resizeObserver.observe(document.body)
    }
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateDeviceType)
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  })

  const isDesktop = computed(() => deviceType.value === 'desktop')
  const isTablet = computed(() => deviceType.value === 'tablet')
  const isMobile = computed(() => deviceType.value === 'mobile')

  const isSmallScreen = computed(() => screenWidth.value < breakpoints.md)
  const isMediumScreen = computed(() => screenWidth.value >= breakpoints.md && screenWidth.value < breakpoints.lg)
  const isLargeScreen = computed(() => screenWidth.value >= breakpoints.lg)

  const breakpoint = computed(() => {
    const width = screenWidth.value
    if (width >= breakpoints['2xl']) return '2xl'
    if (width >= breakpoints.xl) return 'xl'
    if (width >= breakpoints.lg) return 'lg'
    if (width >= breakpoints.md) return 'md'
    if (width >= breakpoints.sm) return 'sm'
    return 'xs'
  })

  const viewport = computed(() => ({
    width: screenWidth.value,
    height: screenHeight.value,
    breakpoint: breakpoint.value,
    deviceType: deviceType.value,
    isTouch: isTouch.value,
    isDesktopApp: isDesktopApp.value,
    platform: platform.value,
  }))

  /**
   * 获取响应式类名
   * 
   * @param {Object} classes - 各断点的类名配置
   * @returns {string} 合并后的类名
   */
  function responsiveClass(classes) {
    const bp = breakpoint.value
    const result = []
    
    // 基础类（所有断点）
    if (classes.base) {
      result.push(classes.base)
    }
    
    // 根据当前断点添加对应类
    if (classes[bp]) {
      result.push(classes[bp])
    }
    
    // 添加设备类型类
    if (classes[deviceType.value]) {
      result.push(classes[deviceType.value])
    }
    
    return result.join(' ')
  }

  /**
   * 获取响应式样式
   * 
   * @param {Object} styles - 各断点的样式配置
   * @returns {Object} 合并后的样式对象
   */
  function responsiveStyle(styles) {
    const bp = breakpoint.value
    const result = {}
    
    // 基础样式（所有断点）
    if (styles.base) {
      Object.assign(result, styles.base)
    }
    
    // 根据当前断点添加对应样式
    if (styles[bp]) {
      Object.assign(result, styles[bp])
    }
    
    // 添加设备类型样式
    if (styles[deviceType.value]) {
      Object.assign(result, styles[deviceType.value])
    }
    
    return result
  }

  /**
   * 延迟执行（针对移动端性能优化）
   * 
   * @param {Function} fn - 要执行的函数
   * @param {number} delay - 延迟时间（毫秒），默认为 100ms
   * @returns {number} timeout ID
   */
  function debounceForMobile(fn, delay = 100) {
    if (isMobile.value) {
      return setTimeout(fn, delay)
    }
    fn()
    return null
  }

  /**
   * 检查是否支持特定功能
   * 
   * @param {string} feature - 功能名称
   * @returns {boolean} 是否支持
   */
  function supportsFeature(feature) {
    switch (feature) {
      case 'touch':
        return isTouch.value
      case 'desktop-app':
        return isDesktopApp.value
      case 'notifications':
        return 'Notification' in window
      case 'clipboard':
        return 'clipboard' in navigator
      case 'fullscreen':
        return 'requestFullscreen' in document.documentElement
      default:
        return false
    }
  }

  /**
   * 获取平台特定的操作提示
   * 
   * @returns {Object} 操作提示对象
   */
  const platformHints = computed(() => {
    if (isTouch.value) {
      return {
        click: '轻触',
        doubleClick: '双击',
        rightClick: '长按',
        scroll: '滑动',
        zoom: '双指缩放',
      }
    }
    return {
      click: '点击',
      doubleClick: '双击',
      rightClick: '右键点击',
      scroll: '滚动',
      zoom: '滚轮缩放',
    }
  })

  return {
    // 基础状态
    deviceType,
    screenWidth,
    screenHeight,
    isTouch,
    isDesktopApp,
    platform,
    
    // 计算属性
    isDesktop,
    isTablet,
    isMobile,
    isSmallScreen,
    isMediumScreen,
    isLargeScreen,
    breakpoint,
    viewport,
    platformHints,
    
    // 配置
    breakpoints,
    
    // 方法
    updateDeviceType,
    responsiveClass,
    responsiveStyle,
    debounceForMobile,
    supportsFeature,
  }
}

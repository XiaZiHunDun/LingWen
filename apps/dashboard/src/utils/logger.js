const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  SILENT: 4,
};

const currentLevel = import.meta.env.VITE_LOG_LEVEL
  ? LOG_LEVELS[import.meta.env.VITE_LOG_LEVEL.toUpperCase()] || LOG_LEVELS.WARN
  : LOG_LEVELS.WARN;

function shouldLog(level) {
  return level >= currentLevel;
}

function serializeArg(arg) {
  if (arg instanceof Error) {
    return {
      message: arg.message,
      stack: arg.stack,
      name: arg.name,
    };
  }
  if (typeof arg === 'object' && arg !== null) {
    try {
      return JSON.parse(JSON.stringify(arg));
    } catch {
      return String(arg);
    }
  }
  return arg;
}

function formatMessage(prefix, message, ...args) {
  const timestamp = new Date().toISOString();
  const formattedArgs = args.length > 0 ? ' ' + JSON.stringify(args.map(serializeArg)) : '';
  return `[${timestamp}] ${prefix} ${message}${formattedArgs}`;
}

export const logger = {
  debug(message, ...args) {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      console.debug(formatMessage('[DEBUG]', message, ...args));
    }
  },

  info(message, ...args) {
    if (shouldLog(LOG_LEVELS.INFO)) {
      console.info(formatMessage('[INFO]', message, ...args));
    }
  },

  warn(message, ...args) {
    if (shouldLog(LOG_LEVELS.WARN)) {
      console.warn(formatMessage('[WARN]', message, ...args));
    }
  },

  error(message, ...args) {
    if (shouldLog(LOG_LEVELS.ERROR)) {
      console.error(formatMessage('[ERROR]', message, ...args));
    }
  },

  log(message, ...args) {
    this.info(message, ...args);
  },

  group(label) {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      console.group(label);
    }
  },

  groupEnd() {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      console.groupEnd();
    }
  },
};

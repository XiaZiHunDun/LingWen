/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // better-sqlite3 是带原生绑定的 CommonJS 依赖，必须由 Node 侧 require，不能被打包。
  serverExternalPackages: ['better-sqlite3'],
  experimental: {
    serverActions: {
      bodySizeLimit: '4mb',
    },
  },
  webpack: (config) => {
    // 本项目按 TS 的 NodeNext 约定用 `@/lib/xxx.js` 引用 .ts 源文件
    // （如 @/lib/llm.js → src/lib/llm.ts），webpack 需要 extensionAlias 才能解析。
    config.resolve.extensionAlias = {
      ...(config.resolve.extensionAlias ?? {}),
      '.js': ['.js', '.ts', '.tsx'],
    };
    return config;
  },
};

export default nextConfig;

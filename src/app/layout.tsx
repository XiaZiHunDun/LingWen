import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "灵文 · AI 小说工作台",
    template: "%s · 灵文",
  },
  description:
    "灵文 LingWen 是一个面向长篇小说的 AI 写作工作台：大纲、章节、字数统计与提示词一站式管理。",
  applicationName: "灵文 LingWen",
  keywords: ["灵文", "LingWen", "AI 写作", "小说", "长篇小说", "章节管理", "大纲"],
  authors: [{ name: "灵文 LingWen" }],
  creator: "灵文 LingWen",
  openGraph: {
    title: "灵文 · AI 小说工作台",
    description:
      "大纲、章节、字数统计与提示词一站式管理，让长篇创作章章可续。",
    locale: "zh_CN",
    type: "website",
    siteName: "灵文 LingWen",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0f1115",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="app-shell">
          <header className="app-header">
            <span className="app-brand">灵文</span>
            <span className="app-tagline">AI 小说工作台</span>
          </header>
          <main className="app-main">{children}</main>
          <footer className="app-footer">灵文 LingWen · 长篇创作，章章可续</footer>
        </div>
      </body>
    </html>
  );
}

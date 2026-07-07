/// <reference types="vitest/globals" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

/** jsdom test ergonomics — not for production src */
interface Element {
  value?: string;
  open?: boolean;
  disabled?: boolean;
  style?: CSSStyleDeclaration;
}

declare class SpeechSynthesisUtterance {
  text: string;
  lang: string;
  constructor(text?: string);
}

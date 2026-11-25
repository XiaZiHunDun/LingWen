export type ID = string;

export type ChapterStatus = 'draft' | 'final';

export interface Project {
  id: ID;
  title: string;
  genre: string;
  style: string;
  synopsis: string;
  targetWords: number;
  createdAt: string;
  updatedAt: string;
}

export interface Chapter {
  id: ID;
  projectId: ID;
  title: string;
  content: string;
  order: number;
  status: ChapterStatus;
  createdAt: string;
  updatedAt: string;
}

export interface Character {
  id: ID;
  projectId: ID;
  name: string;
  role: string;
  traits: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorldEntry {
  id: ID;
  projectId: ID;
  category: string;
  name: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface Database {
  version: number;
  projects: Project[];
  chapters: Chapter[];
  characters: Character[];
  entries: WorldEntry[];
}

export interface ProjectBundle {
  project: Project;
  chapters: Chapter[];
  characters: Character[];
  entries: WorldEntry[];
  stats: ProjectStats;
}

export interface ProjectStats {
  chapterCount: number;
  wordCount: number;
  charCount: number;
  targetWords: number;
  progress: number;
  todayWords: number;
  readingMinutes: number;
}

export type AiMode =
  | 'continue'
  | 'polish'
  | 'expand'
  | 'outline'
  | 'character'
  | 'summary';

export interface AiRequest {
  projectId: ID;
  mode: AiMode;
  instruction?: string;
  chapterId?: ID;
  selection?: string;
  text?: string;
}

export interface AiResponse {
  ok: boolean;
  mode: AiMode;
  provider: 'local' | 'remote';
  text: string;
  note?: string;
  error?: string;
}

export interface OutlineItem {
  title: string;
  summary: string;
}

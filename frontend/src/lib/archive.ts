import { api } from "@/lib/api";

export type ArchiveDashboard = {
  course_count: number;
  video_count: number;
  published_video_count: number;
  draft_video_count: number;
};

export type ArchiveCourse = {
  id: number;
  name: string;
  is_published: boolean;
  website_published: boolean;
  video_count: number;
  website_url: string | null;
};

export type ArchiveVideo = {
  id: number;
  name: string;
  url: string | null;
  video_url: string | null;
  youtube_id: string | null;
  description: string | null;
  course: [number, string] | null;
  is_published: boolean;
  website_published: boolean;
  website_url: string | null;
  tags: unknown[];
};

export type YouTubePreview = {
  url: string;
  video_id: string;
  title: string | null;
  author_name: string | null;
  thumbnail_url: string | null;
  provider_name: string | null;
  fetched: boolean;
};

export async function login(password: string) {
  const response = await api.post<{ access_token: string }>("/api/v1/auth/login", { password });
  return response.data;
}

export async function fetchDashboard() {
  const response = await api.get<ArchiveDashboard>("/api/v1/archive/dashboard");
  return response.data;
}

export async function fetchCourses() {
  const response = await api.get<ArchiveCourse[]>("/api/v1/archive/courses");
  return response.data;
}

export async function fetchVideos() {
  const response = await api.get<ArchiveVideo[]>("/api/v1/archive/youtube/videos");
  return response.data;
}

export async function previewYouTube(url: string) {
  const response = await api.post<YouTubePreview>("/api/v1/archive/youtube/preview", { url });
  return response.data;
}

export async function createYouTubeVideo(payload: {
  url: string;
  course_name: string;
  title: string;
  description: string;
  publish: boolean;
  tags: string[];
}) {
  const response = await api.post<ArchiveVideo>("/api/v1/archive/youtube/videos", payload);
  return response.data;
}

import { api } from "@/lib/api";

export type KnowledgeCategory = {
  id: number;
  name: string;
  complete_name: string | null;
  article_count: number;
  active: boolean;
};

export type KnowledgeArticle = {
  id: number;
  article_ref: string | null;
  name: string;
  state: string;
  category: [number, string] | null;
  owner_agent: [number, string] | null;
  task: [number, string] | null;
  version: number;
  published_at: string | null;
};

export async function fetchKnowledgeCategories() {
  const response = await api.get<KnowledgeCategory[]>("/api/v1/knowledge/categories");
  return response.data;
}

export async function createKnowledgeCategory(payload: {
  name: string;
  description?: string;
  parent_id?: number;
}) {
  const response = await api.post<KnowledgeCategory>("/api/v1/knowledge/categories", payload);
  return response.data;
}

export async function fetchKnowledgeArticles(state?: string) {
  const response = await api.get<KnowledgeArticle[]>("/api/v1/knowledge/articles", {
    params: state ? { state } : {},
  });
  return response.data;
}

export async function createKnowledgeArticle(payload: {
  name: string;
  summary?: string;
  content_html?: string;
  category_id?: number;
  task_id?: number;
}) {
  const response = await api.post<KnowledgeArticle>("/api/v1/knowledge/articles", payload);
  return response.data;
}

export async function transitionKnowledgeArticle(
  articleId: number,
  action: "submit_review" | "publish" | "archive" | "reset_draft",
) {
  const response = await api.post<KnowledgeArticle>(
    `/api/v1/knowledge/articles/${articleId}/transition`,
    { action },
  );
  return response.data;
}

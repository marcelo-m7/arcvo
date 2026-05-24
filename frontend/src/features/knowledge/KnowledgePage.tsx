import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CheckCircle2, Loader2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import {
  createKnowledgeArticle,
  createKnowledgeCategory,
  fetchKnowledgeArticles,
  fetchKnowledgeCategories,
  transitionKnowledgeArticle,
} from "@/lib/knowledge";

export function KnowledgePage() {
  const queryClient = useQueryClient();
  const [articleName, setArticleName] = useState("");
  const [articleSummary, setArticleSummary] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [newCategory, setNewCategory] = useState("");

  const categories = useQuery({
    queryKey: ["knowledge-categories"],
    queryFn: fetchKnowledgeCategories,
  });
  const articles = useQuery({
    queryKey: ["knowledge-articles"],
    queryFn: () => fetchKnowledgeArticles(),
  });

  const createCategory = useMutation({
    mutationFn: createKnowledgeCategory,
    onSuccess: () => {
      setNewCategory("");
      void queryClient.invalidateQueries({ queryKey: ["knowledge-categories"] });
    },
  });

  const createArticle = useMutation({
    mutationFn: createKnowledgeArticle,
    onSuccess: () => {
      setArticleName("");
      setArticleSummary("");
      void queryClient.invalidateQueries({ queryKey: ["knowledge-articles"] });
    },
  });

  const transition = useMutation({
    mutationFn: ({ articleId, action }: { articleId: number; action: "submit_review" | "publish" }) =>
      transitionKnowledgeArticle(articleId, action),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["knowledge-articles"] });
    },
  });

  const categoryRows = useMemo(() => categories.data ?? [], [categories.data]);
  const articleRows = useMemo(() => articles.data ?? [], [articles.data]);

  function onCreateCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createCategory.mutate({ name: newCategory });
  }

  function onCreateArticle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createArticle.mutate({
      name: articleName,
      summary: articleSummary,
      category_id: categoryId ? Number(categoryId) : undefined,
    });
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-md bg-zinc-950 px-5 py-7 text-white sm:px-8">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-yellow-200" aria-hidden />
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-yellow-200">
            arcvo knowledge
          </p>
        </div>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Base de conhecimento operacional.</h2>
        <p className="mt-3 max-w-2xl text-sm text-white/75">
          Artigos vinculados a tickets e tarefas para retenção de contexto técnico.
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="space-y-6">
          <form onSubmit={onCreateCategory} className="rounded-md border border-zinc-200 bg-white p-4">
            <h3 className="text-sm font-semibold">Nova categoria</h3>
            <input
              value={newCategory}
              onChange={(event) => setNewCategory(event.target.value)}
              className="mt-3 h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              placeholder="Ex: Operações"
            />
            <button
              type="submit"
              disabled={!newCategory.trim() || createCategory.isPending}
              className="mt-3 inline-flex h-10 w-full items-center justify-center rounded-md bg-zinc-950 text-sm font-semibold text-white disabled:opacity-60"
            >
              {createCategory.isPending ? "Criando..." : "Criar categoria"}
            </button>
          </form>

          <form onSubmit={onCreateArticle} className="rounded-md border border-zinc-200 bg-white p-4">
            <h3 className="text-sm font-semibold">Novo artigo</h3>
            <input
              value={articleName}
              onChange={(event) => setArticleName(event.target.value)}
              className="mt-3 h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
              placeholder="Título do artigo"
            />
            <textarea
              value={articleSummary}
              onChange={(event) => setArticleSummary(event.target.value)}
              rows={4}
              className="mt-3 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
              placeholder="Resumo"
            />
            <select
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              className="mt-3 h-10 w-full rounded-md border border-zinc-300 px-3 text-sm"
            >
              <option value="">Sem categoria</option>
              {categoryRows.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.complete_name ?? category.name}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!articleName.trim() || createArticle.isPending}
              className="mt-3 inline-flex h-10 w-full items-center justify-center rounded-md bg-zinc-950 text-sm font-semibold text-white disabled:opacity-60"
            >
              {createArticle.isPending ? "Criando..." : "Criar artigo"}
            </button>
          </form>
        </div>

        <div className="rounded-md border border-zinc-200 bg-white">
          <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
            <h3 className="text-sm font-semibold">Artigos</h3>
            {articles.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          </div>
          <div className="divide-y divide-zinc-100">
            {articleRows.map((article) => (
              <article key={article.id} className="px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-zinc-900">
                    {article.article_ref ?? "-"} - {article.name}
                  </p>
                  <span className="rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                    {article.state}
                  </span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  Categoria: {article.category?.[1] ?? "Sem categoria"} | Versão: {article.version}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="inline-flex h-8 items-center gap-1 rounded-md border border-zinc-300 px-2 text-xs"
                    onClick={() => transition.mutate({ articleId: article.id, action: "submit_review" })}
                  >
                    Revisar
                  </button>
                  <button
                    type="button"
                    className="inline-flex h-8 items-center gap-1 rounded-md border border-zinc-300 px-2 text-xs"
                    onClick={() => transition.mutate({ articleId: article.id, action: "publish" })}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" /> Publicar
                  </button>
                </div>
              </article>
            ))}
            {!articles.isLoading && articleRows.length === 0 ? (
              <p className="px-4 py-8 text-sm text-zinc-500">Nenhum artigo cadastrado.</p>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

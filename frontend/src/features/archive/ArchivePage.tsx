import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRight,
  BadgeCheck,
  BookOpen,
  Clapperboard,
  Eye,
  EyeOff,
  Link,
  Loader2,
  Plus,
  RefreshCw,
  Send,
  Tags,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import {
  createYouTubeVideo,
  fetchCourses,
  fetchDashboard,
  fetchVideos,
  previewYouTube,
  type ArchiveCourse,
  type ArchiveVideo,
  type YouTubePreview,
} from "@/lib/archive";

type FormState = {
  url: string;
  courseName: string;
  title: string;
  description: string;
  tags: string;
  publish: boolean;
};

const initialForm: FormState = {
  url: "",
  courseName: "",
  title: "",
  description: "",
  tags: "",
  publish: false,
};

export function ArchivePage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FormState>(initialForm);
  const [preview, setPreview] = useState<YouTubePreview | null>(null);

  const dashboard = useQuery({ queryKey: ["archive-dashboard"], queryFn: fetchDashboard });
  const courses = useQuery({ queryKey: ["archive-courses"], queryFn: fetchCourses });
  const videos = useQuery({ queryKey: ["archive-videos"], queryFn: fetchVideos });

  const previewMutation = useMutation({
    mutationFn: previewYouTube,
    onSuccess: (data) => {
      setPreview(data);
      setForm((current) => ({
        ...current,
        url: data.url,
        title: current.title || data.title || "",
      }));
    },
  });

  const createMutation = useMutation({
    mutationFn: createYouTubeVideo,
    onSuccess: () => {
      setForm(initialForm);
      setPreview(null);
      void queryClient.invalidateQueries({ queryKey: ["archive-dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["archive-courses"] });
      void queryClient.invalidateQueries({ queryKey: ["archive-videos"] });
    },
  });

  const suggestedCourses = useMemo(() => courses.data ?? [], [courses.data]);

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function onPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    previewMutation.mutate(form.url);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createMutation.mutate({
      url: preview?.url || form.url,
      course_name: form.courseName,
      title: form.title,
      description: form.description,
      publish: form.publish,
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
    });
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="relative overflow-hidden rounded-md bg-zinc-950 px-5 py-8 text-white sm:px-8">
        <img
          src="https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1600&q=80"
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-35"
        />
        <div className="absolute inset-0 bg-[linear-gradient(110deg,rgba(8,20,20,.96),rgba(8,20,20,.7)_42%,rgba(236,72,153,.25))]" />
        <div className="relative grid gap-8 lg:grid-cols-[1fr_360px] lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-yellow-300">
              acervo youtube + odoo elearning
            </p>
            <h2 className="mt-3 max-w-3xl text-4xl font-black leading-tight sm:text-5xl">
              Cursos como territorio, videos como memoria.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/80">
              Cole URLs, organize por categoria e envie tudo para o modulo eLearning do Odoo.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Cursos" value={dashboard.data?.course_count ?? 0} icon={BookOpen} />
            <Stat label="Videos" value={dashboard.data?.video_count ?? 0} icon={Clapperboard} />
            <Stat
              label="Publicados"
              value={dashboard.data?.published_video_count ?? 0}
              icon={Eye}
            />
            <Stat label="Rascunhos" value={dashboard.data?.draft_video_count ?? 0} icon={EyeOff} />
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="rounded-md border border-zinc-200 bg-white">
          <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
            <div className="flex items-center gap-2">
              <Send className="h-4 w-4 text-emerald-700" aria-hidden />
              <h3 className="text-sm font-semibold">Enviar video</h3>
            </div>
            <span className="rounded-full bg-yellow-100 px-2.5 py-1 text-xs font-medium text-yellow-900">
              rascunho por padrao
            </span>
          </div>

          <div className="grid gap-px bg-zinc-200 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="bg-white p-4 sm:p-5">
              <form onSubmit={onPreview} className="space-y-4">
                <TextInput
                  label="URL do YouTube"
                  value={form.url}
                  onChange={(value) => updateForm("url", value)}
                  placeholder="https://youtu.be/..."
                />
                <button
                  type="submit"
                  disabled={!form.url || previewMutation.isPending}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {previewMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  ) : (
                    <RefreshCw className="h-4 w-4" aria-hidden />
                  )}
                  Buscar metadados
                </button>
              </form>

              <form onSubmit={onSubmit} className="mt-6 space-y-4">
                <TextInput
                  label="Curso / categoria"
                  value={form.courseName}
                  onChange={(value) => updateForm("courseName", value)}
                  placeholder="Ex: Pajuba, Axe, Historia viva"
                  list="course-suggestions"
                />
                <datalist id="course-suggestions">
                  {suggestedCourses.map((course) => (
                    <option value={course.name} key={course.id} />
                  ))}
                </datalist>
                <TextInput
                  label="Titulo"
                  value={form.title}
                  onChange={(value) => updateForm("title", value)}
                  placeholder="Titulo do video"
                />
                <label className="block">
                  <span className="text-sm font-medium text-zinc-700">Descricao</span>
                  <textarea
                    value={form.description}
                    onChange={(event) => updateForm("description", event.target.value)}
                    rows={4}
                    className="mt-2 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-emerald-600 focus:ring-2"
                  />
                </label>
                <TextInput
                  label="Tags"
                  value={form.tags}
                  onChange={(value) => updateForm("tags", value)}
                  placeholder="separe por virgulas"
                />
                <label className="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50 px-3 py-3">
                  <span>
                    <span className="block text-sm font-medium text-zinc-900">Publicar agora</span>
                    <span className="block text-xs text-zinc-500">Liga visibilidade no eLearning.</span>
                  </span>
                  <input
                    type="checkbox"
                    checked={form.publish}
                    onChange={(event) => updateForm("publish", event.target.checked)}
                    className="h-5 w-5 accent-emerald-700"
                  />
                </label>

                {createMutation.isError ? (
                  <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                    Nao foi possivel enviar o video. Confira os campos e a conexao Odoo.
                  </p>
                ) : null}
                {createMutation.isSuccess ? (
                  <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    Video enviado para o eLearning.
                  </p>
                ) : null}

                <button
                  type="submit"
                  disabled={
                    createMutation.isPending || !form.url || !form.courseName || !form.title
                  }
                  className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-semibold text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {createMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  ) : (
                    <Plus className="h-4 w-4" aria-hidden />
                  )}
                  Enviar para Odoo
                </button>
              </form>
            </div>

            <aside className="bg-[#fff8df] p-4 sm:p-5">
              <PreviewCard preview={preview} />
            </aside>
          </div>
        </div>

        <CoursesPanel courses={courses.data ?? []} loading={courses.isLoading} />
      </section>

      <VideosPanel videos={videos.data ?? []} loading={videos.isLoading} />
    </div>
  );
}

function Stat({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: typeof BookOpen;
}) {
  return (
    <div className="rounded-md border border-white/15 bg-white/10 p-3 backdrop-blur">
      <Icon className="h-4 w-4 text-yellow-300" aria-hidden />
      <p className="mt-3 text-2xl font-bold">{value}</p>
      <p className="text-xs text-white/70">{label}</p>
    </div>
  );
}

function TextInput({
  label,
  value,
  onChange,
  placeholder,
  list,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  list?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-zinc-700">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        list={list}
        className="mt-2 h-11 w-full rounded-md border border-zinc-300 px-3 text-sm outline-none ring-emerald-600 focus:ring-2"
      />
    </label>
  );
}

function PreviewCard({ preview }: { preview: YouTubePreview | null }) {
  if (!preview) {
    return (
      <div className="flex h-full min-h-72 flex-col justify-between rounded-md border border-yellow-200 bg-white/70 p-4">
        <div>
          <Link className="h-5 w-5 text-pink-700" aria-hidden />
          <h4 className="mt-4 text-lg font-bold">Preview do YouTube</h4>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Cole uma URL para puxar titulo, canal e thumbnail publica via oEmbed.
          </p>
        </div>
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">
          sem api key
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-yellow-200 bg-white">
      {preview.thumbnail_url ? (
        <img src={preview.thumbnail_url} alt="" className="aspect-video w-full object-cover" />
      ) : (
        <div className="flex aspect-video items-center justify-center bg-zinc-900 text-white">
          <Clapperboard className="h-8 w-8" aria-hidden />
        </div>
      )}
      <div className="space-y-3 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pink-700">
          {preview.fetched ? "metadados encontrados" : "fallback manual"}
        </p>
        <h4 className="font-semibold leading-6">{preview.title || "Titulo manual necessario"}</h4>
        <p className="text-sm text-zinc-600">{preview.author_name || "Canal nao identificado"}</p>
        <p className="break-all text-xs text-zinc-500">{preview.url}</p>
      </div>
    </div>
  );
}

function CoursesPanel({ courses, loading }: { courses: ArchiveCourse[]; loading: boolean }) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white">
      <div className="flex items-center gap-2 border-b border-zinc-200 px-4 py-3">
        <BookOpen className="h-4 w-4 text-emerald-700" aria-hidden />
        <h3 className="text-sm font-semibold">Cursos / categorias</h3>
      </div>
      <div className="divide-y divide-zinc-100">
        {loading ? <PanelLoading /> : null}
        {!loading && courses.length === 0 ? <Empty label="Nenhum curso criado ainda." /> : null}
        {courses.map((course) => (
          <div key={course.id} className="flex items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="font-medium">{course.name}</p>
              <p className="text-xs text-zinc-500">{course.video_count} videos</p>
            </div>
            <StatusPill published={course.is_published || course.website_published} />
          </div>
        ))}
      </div>
    </section>
  );
}

function VideosPanel({ videos, loading }: { videos: ArchiveVideo[]; loading: boolean }) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <Clapperboard className="h-4 w-4 text-emerald-700" aria-hidden />
          <h3 className="text-sm font-semibold">Videos no eLearning</h3>
        </div>
        <Tags className="h-4 w-4 text-pink-700" aria-hidden />
      </div>
      <div className="divide-y divide-zinc-100">
        {loading ? <PanelLoading /> : null}
        {!loading && videos.length === 0 ? <Empty label="Nenhum video enviado ainda." /> : null}
        {videos.map((video) => (
          <article key={video.id} className="grid gap-3 px-4 py-4 md:grid-cols-[1fr_auto]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-semibold">{video.name}</h4>
                <StatusPill published={video.is_published || video.website_published} />
              </div>
              <p className="mt-1 text-sm text-zinc-500">{video.course?.[1] ?? "Sem curso"}</p>
              <p className="mt-2 line-clamp-2 text-sm text-zinc-600">
                {video.description || "Sem descricao."}
              </p>
            </div>
            <div className="flex items-center gap-2 md:justify-end">
              {video.website_url ? (
                <a
                  href={video.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50"
                >
                  Abrir
                  <ArrowUpRight className="h-4 w-4" aria-hidden />
                </a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function StatusPill({ published }: { published: boolean }) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        published ? "bg-emerald-100 text-emerald-800" : "bg-zinc-100 text-zinc-600",
      ].join(" ")}
    >
      {published ? <BadgeCheck className="h-3 w-3" aria-hidden /> : <EyeOff className="h-3 w-3" />}
      {published ? "publicado" : "rascunho"}
    </span>
  );
}

function PanelLoading() {
  return (
    <div className="flex items-center gap-2 px-4 py-5 text-sm text-zinc-500">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      Carregando
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return <p className="px-4 py-5 text-sm text-zinc-500">{label}</p>;
}

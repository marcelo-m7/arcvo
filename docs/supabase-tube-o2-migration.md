# Supabase Migration Playbook (tube-o2 Stable)

This document defines the standard workflow to converge a Supabase project to the stable tube-o2 baseline from this repository.

## Source of Truth

Use only these paths as source:

- `frontend/tube-o2/supabase/migrations`
- `frontend/tube-o2/supabase/functions`
- `frontend/tube-o2/src/integrations/supabase/types.ts` (validation reference)

Current public schema baseline:

- `categories`
- `profiles`
- `videos`
- `favorites`
- `playlists`
- `playlist_videos`
- `playlist_collaborators`
- `playlist_progress`
- `ai_enrichments`
- `comments`
- `video_view_events`

Current Edge Functions baseline:

- `enrich-video`
- `import-youtube-playlist`
- `mark-top-featured`

## Pre-Flight Checklist

1. Inspect current remote state first:
   - `mcp_supabase_list_tables` (schema `public`)
   - `mcp_supabase_list_migrations`
   - `mcp_supabase_list_edge_functions`
2. Run advisors before changing schema:
   - `mcp_supabase_get_advisors` with `security`
   - `mcp_supabase_get_advisors` with `performance`
3. Confirm changelog-sensitive behavior when needed:
   - `https://supabase.com/changelog.md`

## Migration Strategy

Use one convergence migration through `mcp_supabase_apply_migration` that:

1. Drops incompatible legacy `public` tables/views from previous app models.
2. Recreates the tube-o2 stable schema, indexes, policies, triggers, and RPCs.
3. Recreates storage bucket/policies used by tube-o2 (`avatars`).
4. Preserves RLS on all `public` tables.

Notes:

- Prefer a convergence migration over replaying every historical file in this folder, because older files include experimental/duplicate steps.
- Some historical migrations are not safe to replay as-is (missing dependencies or references to removed tables).

## Post-Migration Validation

Run these checks after `apply_migration`:

1. Tables and RLS:
   - `mcp_supabase_list_tables` (public)
2. Views expected for tube-o2 stable:
   - `SELECT table_name FROM information_schema.views WHERE table_schema='public';`
   - Expected result: no required views for this baseline.
3. RPC presence:
   - `increment_video_view_count`
   - `mark_top_videos_as_featured`
   - `list_featured_videos`
   - `delete_user_account`
   - `update_playlist_derived_fields`
   - `update_playlist_thumbnail_from_first_video`
   - `playlist_accessible_to_user`
4. Re-run advisors and review findings.

## Edge Functions Deployment

Deploy with `mcp_supabase_deploy_edge_function` from `frontend/tube-o2/supabase/functions`.

Recommended configuration for this baseline:

- `enrich-video`: `verify_jwt=false` (manual auth in handler)
- `import-youtube-playlist`: `verify_jwt=false` (manual auth in handler)
- `mark-top-featured`: `verify_jwt=false` (handler checks auth header)

Environment variables expected by functions:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY` (enrich-video)
- `OPENAI_MODEL` (optional, enrich-video)
- `YOUTUBE_API_KEY` (import-youtube-playlist)

## Operational Caveats

- New functions are deployed by version. Old function slugs are not removed automatically by this workflow.
- If remote still contains unrelated function slugs, document them and remove manually in Supabase dashboard if needed.
- Keep `service_role` keys out of client-side apps.

## Arcvo Convention

When a task says "migrate Supabase to tube-o2 stable":

1. Use this playbook.
2. Apply schema changes through `mcp_supabase_apply_migration`.
3. Deploy the three baseline functions.
4. Return a checklist-style report with:
   - applied migration name
   - resulting public tables
   - function slugs and versions
   - advisor findings

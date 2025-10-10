-- =========================================================
-- Supabase DDL: KetoHelper Core Schema
-- Safe to run multiple times (IF NOT EXISTS where possible)
-- =========================================================
BEGIN;

-- ---------- Extensions ----------
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector (for embeddings)
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram search

-- ---------- Enum Types ----------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'access_state') THEN
    CREATE TYPE access_state AS ENUM ('none','trial','paid');
  END IF;
END$$;

-- ---------- Utility: auto-update updated_at ----------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- =========================================================
-- 1) Users & Identity
-- =========================================================
CREATE TABLE IF NOT EXISTS public.users (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email                varchar(255),
  nickname             varchar(255),
  profile_image_url    text,
  profile_image_source varchar(50) NOT NULL DEFAULT 'default',
  first_login          boolean NOT NULL DEFAULT true,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),
  trial_granted        boolean NOT NULL DEFAULT true,
  trial_start_at       timestamptz NOT NULL DEFAULT now(),
  trial_end_at         timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
  paid_until           timestamptz,
  access_state         access_state NOT NULL DEFAULT 'trial',
  goals_kcal           integer,
  goals_carbs_g        integer,
  selected_allergy_ids integer[] DEFAULT '{}',
  selected_dislike_ids integer[] DEFAULT '{}',
  social_nickname      text
);

-- indexes matching provided spec
CREATE UNIQUE INDEX IF NOT EXISTS users_pkey ON public.users (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_lower ON public.users (lower(email)) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_trial_end_at ON public.users (trial_end_at);
CREATE INDEX IF NOT EXISTS idx_users_paid_until ON public.users (paid_until);
CREATE INDEX IF NOT EXISTS idx_users_access_state ON public.users (access_state);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);
CREATE INDEX IF NOT EXISTS idx_users_selected_allergy_ids ON public.users USING gin (selected_allergy_ids);
CREATE INDEX IF NOT EXISTS idx_users_selected_dislike_ids ON public.users USING gin (selected_dislike_ids);

-- trigger
DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- user_identity
CREATE TABLE IF NOT EXISTS public.user_identity (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid NOT NULL REFERENCES public.users(id),
  provider         varchar(30) NOT NULL,
  provider_user_id varchar(255) NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_provider_uid UNIQUE (provider, provider_user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS user_identity_pkey ON public.user_identity (id);
CREATE INDEX IF NOT EXISTS idx_uid_user ON public.user_identity (user_id);

DROP TRIGGER IF EXISTS trg_user_identity_updated_at ON public.user_identity;
CREATE TRIGGER trg_user_identity_updated_at
BEFORE UPDATE ON public.user_identity
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 2) Allergy / Dislike Masters
-- =========================================================
-- allergy_master (id: identity int)
CREATE TABLE IF NOT EXISTS public.allergy_master (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name            varchar(100) NOT NULL,
  description     text,
  category        varchar(50),
  severity_level  integer DEFAULT 1,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT allergy_master_name_key UNIQUE (name)
);

CREATE UNIQUE INDEX IF NOT EXISTS allergy_master_pkey ON public.allergy_master (id);
CREATE UNIQUE INDEX IF NOT EXISTS allergy_master_name_key ON public.allergy_master (name);
CREATE INDEX IF NOT EXISTS idx_allergy_master_category ON public.allergy_master (category);

-- dislike_ingredient_master (id: identity int)
CREATE TABLE IF NOT EXISTS public.dislike_ingredient_master (
  id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name        varchar(100) NOT NULL,
  category    varchar(50),
  description text,
  created_at  timestamptz DEFAULT now(),
  CONSTRAINT dislike_ingredient_master_name_key UNIQUE (name)
);

CREATE UNIQUE INDEX IF NOT EXISTS dislike_ingredient_master_pkey ON public.dislike_ingredient_master (id);
CREATE UNIQUE INDEX IF NOT EXISTS dislike_ingredient_master_name_key ON public.dislike_ingredient_master (name);
CREATE INDEX IF NOT EXISTS idx_dislike_master_category ON public.dislike_ingredient_master (category);

-- =========================================================
-- 3) Restaurant / Menu / Ingredients / Scores / Embeddings
-- =========================================================
CREATE TABLE IF NOT EXISTS public.restaurant (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                        text NOT NULL,
  addr_road                   text,
  addr_jibun                  text,
  lat                         double precision NOT NULL,
  lng                         double precision NOT NULL,
  phone                       varchar(30),
  category                    varchar(100),
  price_range                 integer,
  homepage_url                text,
  source                      varchar(50) NOT NULL,
  source_url                  text NOT NULL,
  place_provider              text,
  place_id                    text,
  normalized_name             text,
  created_at                  timestamptz NOT NULL DEFAULT now(),
  updated_at                  timestamptz NOT NULL DEFAULT now(),
  representative_menu_name    text,
  representative_keto_score   integer
);

CREATE UNIQUE INDEX IF NOT EXISTS restaurant_pkey ON public.restaurant (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_restaurant_source_url ON public.restaurant (source, source_url);
CREATE UNIQUE INDEX IF NOT EXISTS ux_restaurant_place ON public.restaurant (place_provider, place_id)
  WHERE place_provider IS NOT NULL AND place_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurant_geo ON public.restaurant (lat, lng);
CREATE INDEX IF NOT EXISTS idx_restaurant_name_addr ON public.restaurant (name, addr_road);
CREATE INDEX IF NOT EXISTS idx_restaurant_norm_name ON public.restaurant (normalized_name);
CREATE INDEX IF NOT EXISTS idx_restaurant_name_trgm ON public.restaurant USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_restaurant_representative_keto_score ON public.restaurant (representative_keto_score);

DROP TRIGGER IF EXISTS trg_restaurant_updated_at ON public.restaurant;
CREATE TRIGGER trg_restaurant_updated_at
BEFORE UPDATE ON public.restaurant
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ingredient
CREATE TABLE IF NOT EXISTS public.ingredient (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text NOT NULL,
  kind       varchar(20) NOT NULL DEFAULT 'ingredient',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ingredient_name_key UNIQUE (name)
);
CREATE UNIQUE INDEX IF NOT EXISTS ingredient_pkey ON public.ingredient (id);
CREATE UNIQUE INDEX IF NOT EXISTS ingredient_name_key ON public.ingredient (name);

-- ingredient_alias
CREATE TABLE IF NOT EXISTS public.ingredient_alias (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id uuid NOT NULL REFERENCES public.ingredient(id),
  alias         text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_ing_alias UNIQUE (ingredient_id, alias)
);
CREATE UNIQUE INDEX IF NOT EXISTS ingredient_alias_pkey ON public.ingredient_alias (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ing_alias ON public.ingredient_alias (ingredient_id, alias);
CREATE INDEX IF NOT EXISTS idx_ing_alias_alias ON public.ingredient_alias (alias);

-- menu
CREATE TABLE IF NOT EXISTS public.menu (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  restaurant_id   uuid NOT NULL REFERENCES public.restaurant(id),
  name            text NOT NULL,
  price           integer,
  currency        varchar(10) NOT NULL DEFAULT 'KRW',
  description     text,
  image_url       text,
  is_signature    boolean NOT NULL DEFAULT false,
  name_norm       text,
  is_side         boolean NOT NULL DEFAULT false,
  last_checked_at timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_menu_restaurant_name UNIQUE (restaurant_id, name)
);
CREATE UNIQUE INDEX IF NOT EXISTS menu_pkey ON public.menu (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_menu_restaurant_name ON public.menu (restaurant_id, name);
CREATE INDEX IF NOT EXISTS idx_menu_restaurant ON public.menu (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_name_norm ON public.menu (name_norm);
CREATE INDEX IF NOT EXISTS idx_menu_name_trgm ON public.menu USING gin (name gin_trgm_ops);

DROP TRIGGER IF EXISTS trg_menu_updated_at ON public.menu;
CREATE TRIGGER trg_menu_updated_at
BEFORE UPDATE ON public.menu
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- menu_ingredient (composite PK)
CREATE TABLE IF NOT EXISTS public.menu_ingredient (
  menu_id      uuid NOT NULL REFERENCES public.menu(id),
  ingredient_id uuid NOT NULL REFERENCES public.ingredient(id),
  role         varchar(20) NOT NULL DEFAULT 'main',
  source       varchar(20) NOT NULL,
  confidence   numeric(5,2) NOT NULL DEFAULT 0.70,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pk_menu_ingredient PRIMARY KEY (menu_id, ingredient_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS pk_menu_ingredient ON public.menu_ingredient (menu_id, ingredient_id);
CREATE INDEX IF NOT EXISTS idx_menu_ing_menu ON public.menu_ingredient (menu_id);
CREATE INDEX IF NOT EXISTS idx_menu_ing_ing ON public.menu_ingredient (ingredient_id);

DROP TRIGGER IF EXISTS trg_menu_ingredient_updated_at ON public.menu_ingredient;
CREATE TRIGGER trg_menu_ingredient_updated_at
BEFORE UPDATE ON public.menu_ingredient
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- menu_embedding
CREATE TABLE IF NOT EXISTS public.menu_embedding (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  menu_id          uuid NOT NULL REFERENCES public.menu(id),
  model_name       varchar(100) NOT NULL DEFAULT 'text-embedding-3-small',
  dimension        integer NOT NULL DEFAULT 1536,
  algorithm_version varchar(40) NOT NULL DEFAULT 'RAG-v1.0',
  embedding        vector(1536),
  content_hash     text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  content_blob     text,
  CONSTRAINT ux_menu_embedding_model UNIQUE (menu_id, model_name, algorithm_version)
);
CREATE UNIQUE INDEX IF NOT EXISTS menu_embedding_pkey ON public.menu_embedding (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_menu_embedding_model ON public.menu_embedding (menu_id, model_name, algorithm_version);
CREATE INDEX IF NOT EXISTS idx_menu_embedding_hash ON public.menu_embedding (content_hash);
CREATE INDEX IF NOT EXISTS idx_menu_embedding_menu ON public.menu_embedding (menu_id);
CREATE INDEX IF NOT EXISTS ix_menu_emb_cosine ON public.menu_embedding USING hnsw (embedding vector_cosine_ops);

DROP TRIGGER IF EXISTS trg_menu_embedding_updated_at ON public.menu_embedding;
CREATE TRIGGER trg_menu_embedding_updated_at
BEFORE UPDATE ON public.menu_embedding
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- keto_scores
CREATE TABLE IF NOT EXISTS public.keto_scores (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  menu_id        uuid NOT NULL REFERENCES public.menu(id),
  score          integer NOT NULL,
  reasons_json   jsonb,
  rule_version   text NOT NULL,
  prompt_version text,
  valid_until    timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS keto_scores_pkey ON public.keto_scores (id);
CREATE INDEX IF NOT EXISTS idx_keto_scores_menu ON public.keto_scores (menu_id);

DROP TRIGGER IF EXISTS trg_keto_scores_updated_at ON public.keto_scores;
CREATE TRIGGER trg_keto_scores_updated_at
BEFORE UPDATE ON public.keto_scores
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 4) Recipes (blob + embedding)
-- =========================================================
CREATE TABLE IF NOT EXISTS public.recipe_blob_emb (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id    uuid,
  title        text,
  blob         jsonb,
  ingredients  text[],
  tags         text[],
  allergens    text[],
  meal_type    varchar(20),
  embedding    vector(1536),
  model_name   varchar(100) NOT NULL DEFAULT 'text-embedding-3-small',
  fingerprint  text NOT NULL,
  content_hash text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),  
  url          text,
  CONSTRAINT ux_recipe_fingerprint UNIQUE (fingerprint)
);

CREATE UNIQUE INDEX IF NOT EXISTS recipe_blob_emb_pkey ON public.recipe_blob_emb (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_recipe_fingerprint ON public.recipe_blob_emb (fingerprint);
CREATE INDEX IF NOT EXISTS idx_recipe_title ON public.recipe_blob_emb (title);
CREATE INDEX IF NOT EXISTS idx_recipe_meal_type ON public.recipe_blob_emb (meal_type);
CREATE INDEX IF NOT EXISTS ix_recipe_emb_cosine ON public.recipe_blob_emb USING hnsw (embedding vector_cosine_ops);

DROP TRIGGER IF EXISTS trg_recipe_blob_emb_updated_at ON public.recipe_blob_emb;
CREATE TRIGGER trg_recipe_blob_emb_updated_at
BEFORE UPDATE ON public.recipe_blob_emb
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 5) Meal Plan / Items / Log
-- =========================================================
CREATE TABLE IF NOT EXISTS public.meal_plan (
  id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id     uuid NOT NULL REFERENCES public.users(id),
  name        varchar(255) NOT NULL,
  description text,
  start_date  date,
  end_date    date,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS meal_plan_pkey ON public.meal_plan (id);
CREATE INDEX IF NOT EXISTS idx_mealplan_user ON public.meal_plan (user_id);

DROP TRIGGER IF EXISTS trg_meal_plan_updated_at ON public.meal_plan;
CREATE TRIGGER trg_meal_plan_updated_at
BEFORE UPDATE ON public.meal_plan
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS public.meal_plan_item (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mealplan_id     integer NOT NULL REFERENCES public.meal_plan(id),
  recipe_blob_id  uuid NOT NULL REFERENCES public.recipe_blob_emb(id),
  recipe_title    varchar(255) NOT NULL,
  meal_type       varchar(20) NOT NULL,
  planned_date    date,
  sort_order      integer,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_mealplanitem_unique UNIQUE (mealplan_id, planned_date, meal_type, recipe_blob_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS meal_plan_item_pkey ON public.meal_plan_item (id);
CREATE INDEX IF NOT EXISTS idx_mealplanitem_plan ON public.meal_plan_item (mealplan_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mealplanitem_unique ON public.meal_plan_item (mealplan_id, planned_date, meal_type, recipe_blob_id);

DROP TRIGGER IF EXISTS trg_meal_plan_item_updated_at ON public.meal_plan_item;
CREATE TRIGGER trg_meal_plan_item_updated_at
BEFORE UPDATE ON public.meal_plan_item
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS public.meal_log (
  id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id     uuid NOT NULL REFERENCES public.users(id),
  mealplan_id integer REFERENCES public.meal_plan(id),
  date        date NOT NULL,
  meal_type   varchar(20) NOT NULL,
  eaten       boolean NOT NULL DEFAULT false,
  note        text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_meallog_uniqueness UNIQUE (user_id, date, meal_type)
);

CREATE UNIQUE INDEX IF NOT EXISTS meal_log_pkey ON public.meal_log (id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_meallog_uniqueness ON public.meal_log (user_id, date, meal_type);
CREATE INDEX IF NOT EXISTS idx_meallog_user ON public.meal_log (user_id);

DROP TRIGGER IF EXISTS trg_meal_log_updated_at ON public.meal_log;
CREATE TRIGGER trg_meal_log_updated_at
BEFORE UPDATE ON public.meal_log
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 6) Docs RAG
-- =========================================================
CREATE TABLE IF NOT EXISTS public.docs_rag (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id     text NOT NULL,
  title      text,
  tags       text[],
  chunk      text NOT NULL,
  embedding  vector(1536),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS docs_rag_pkey ON public.docs_rag (id);
CREATE INDEX IF NOT EXISTS ix_docs_rag_hnsw ON public.docs_rag USING hnsw (embedding vector_cosine_ops);

-- =========================================================
-- 7) Chat & Threads
-- =========================================================
CREATE TABLE IF NOT EXISTS public.chat_thread (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES public.users(id),
  title           text,
  last_message_at timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  guest_id        uuid
);

CREATE UNIQUE INDEX IF NOT EXISTS chat_thread_pkey ON public.chat_thread (id);
CREATE INDEX IF NOT EXISTS idx_chat_thread_user ON public.chat_thread (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_thread_guest ON public.chat_thread (guest_id) WHERE guest_id IS NOT NULL;

DROP TRIGGER IF EXISTS trg_chat_thread_updated_at ON public.chat_thread;
CREATE TRIGGER trg_chat_thread_updated_at
BEFORE UPDATE ON public.chat_thread
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS public.chat (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id         uuid REFERENCES public.users(id),
  thread_id       uuid REFERENCES public.chat_thread(id),
  conversation_id uuid,
  role            varchar(20) NOT NULL,
  message         text NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  guest_id        uuid,
  message_uuid    uuid UNIQUE,
  expires_at      timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS chat_pkey ON public.chat (id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON public.chat (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_thread_order ON public.chat (thread_id, id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_chat_message_uuid ON public.chat (message_uuid);
CREATE INDEX IF NOT EXISTS idx_chat_thread_desc ON public.chat (thread_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_chat_expires ON public.chat (expires_at);
CREATE INDEX IF NOT EXISTS idx_chat_guest ON public.chat (guest_id) WHERE guest_id IS NOT NULL;

DROP TRIGGER IF EXISTS trg_chat_updated_at ON public.chat;
CREATE TRIGGER trg_chat_updated_at
BEFORE UPDATE ON public.chat
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 8) Subscription Events
-- =========================================================
CREATE TABLE IF NOT EXISTS public.subscription_event (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES public.users(id),
  event_type varchar(30) NOT NULL,
  prev_state access_state,
  new_state  access_state,
  note       text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS subscription_event_pkey ON public.subscription_event (id);
CREATE INDEX IF NOT EXISTS idx_sub_event_user ON public.subscription_event (user_id);
CREATE INDEX IF NOT EXISTS idx_sub_event_user_time ON public.subscription_event (user_id, created_at);

COMMIT;

-- =========================================================
-- Notes
-- - Identity columns are used for integer PKs (meal_* / master tables).
-- - HNSW indexes require pgvector >= 0.5 (Supabase supports it).
-- - Triggers keep updated_at fresh on UPDATE.
-- =========================================================

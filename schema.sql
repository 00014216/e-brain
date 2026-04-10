

-- e-brain Database Schema

create extension if not exists "uuid-ossp";

-- Memories

create table if not exists memories (
  id            uuid default uuid_generate_v4() primary key,
  user_id       uuid references auth.users(id) on delete cascade not null,
  title         text,
  content       text not null default '',
  raw_content   text,
  memory_type   text default 'text' check (memory_type in ('text','image','url','screenshot','note')),
  source_url    text,
  source_title  text,
  source_author text,
  image_url     text,
  image_path    text,
  ai_summary    text,
  ai_analysis   text,
  key_insights  text[],
  action_items  text[],
  sentiment     text default 'neutral',
  search_vector tsvector,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

create index if not exists memories_search_idx   on memories using gin(search_vector);
create index if not exists memories_user_idx     on memories(user_id);
create index if not exists memories_created_idx  on memories(created_at desc);
create index if not exists memories_type_idx     on memories(memory_type);

create or replace function update_memory_search_vector()
returns trigger as $$
begin
  new.search_vector :=
    to_tsvector('english',
      coalesce(new.title, '')         || ' ' ||
      coalesce(new.content, '')       || ' ' ||
      coalesce(new.ai_summary, '')    || ' ' ||
      coalesce(new.source_title, '')  || ' ' ||
      coalesce(new.source_author, '')
    );
  new.updated_at := now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists memories_fts_trigger on memories;
create trigger memories_fts_trigger
  before insert or update on memories
  for each row execute function update_memory_search_vector();


-- HAashtags

create table if not exists hashtags (
  id              uuid default uuid_generate_v4() primary key,
  normalized_form text unique not null,
  display_form    text not null,
  usage_count     integer default 0,
  created_at      timestamptz default now()
);

create index if not exists hashtags_normalized_idx on hashtags(normalized_form);


-- Hashtag aliases

create table if not exists hashtag_aliases (
  id                   uuid default uuid_generate_v4() primary key,
  canonical_hashtag_id uuid references hashtags(id) on delete cascade not null,
  alias_normalized     text not null unique,
  created_at           timestamptz default now()
);


-- Memory <-> hashtag many-to-many

create table if not exists memory_hashtags (
  memory_id  uuid references memories(id) on delete cascade not null,
  hashtag_id uuid references hashtags(id) on delete cascade not null,
  primary key (memory_id, hashtag_id)
);

create index if not exists mh_hashtag_idx on memory_hashtags(hashtag_id);
create index if not exists mh_memory_idx  on memory_hashtags(memory_id);


-- entities
-- People, companies, technologies, concepts extracted from memories

create table if not exists entities (
  id              uuid default uuid_generate_v4() primary key,
  user_id         uuid references auth.users(id) on delete cascade not null,
  entity_type     text not null check (entity_type in ('person','company','technology','concept','location','event','other')),
  name            text not null,
  normalized_name text not null,
  description     text,
  metadata        jsonb default '{}',
  mention_count   integer default 0,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  unique(user_id, normalized_name)
);

create index if not exists entities_user_idx on entities(user_id);
create index if not exists entities_type_idx on entities(entity_type);


-- memory <-> entity  (many-to-many)

create table if not exists memory_entities (
  memory_id uuid references memories(id) on delete cascade not null,
  entity_id uuid references entities(id)  on delete cascade not null,
  primary key (memory_id, entity_id)
);

create index if not exists me_entity_idx on memory_entities(entity_id);
create index if not exists me_memory_idx on memory_entities(memory_id);


-- tags
-- User-defined manual labels (separate from AI hashtags)

create table if not exists tags (
  id         uuid default uuid_generate_v4() primary key,
  user_id    uuid references auth.users(id) on delete cascade not null,
  name       text not null,
  color      text default '#6366f1',
  created_at timestamptz default now(),
  unique(user_id, name)
);


-- memory <-> TAg  (many-to-many)

create table if not exists memory_tags (
  memory_id uuid references memories(id) on delete cascade not null,
  tag_id    uuid references tags(id)     on delete cascade not null,
  primary key (memory_id, tag_id)
);

-- user settings

create table if not exists user_settings (
  user_id           uuid references auth.users(id) on delete cascade primary key,
  display_name      text,
  anthropic_api_key text,
  openai_api_key    text,
  preferences       jsonb default '{}',
  updated_at        timestamptz default now()
);


-- Row level security

alter table memories        enable row level security;
alter table entities        enable row level security;
alter table tags            enable row level security;
alter table memory_tags     enable row level security;
alter table memory_hashtags enable row level security;
alter table memory_entities enable row level security;
alter table user_settings   enable row level security;

-- Memories
create policy "own memories select" on memories for select using (auth.uid() = user_id);
create policy "own memories insert" on memories for insert with check (auth.uid() = user_id);
create policy "own memories update" on memories for update using (auth.uid() = user_id);
create policy "own memories delete" on memories for delete using (auth.uid() = user_id);

-- Entities
create policy "own entities select" on entities for select using (auth.uid() = user_id);
create policy "own entities insert" on entities for insert with check (auth.uid() = user_id);
create policy "own entities update" on entities for update using (auth.uid() = user_id);
create policy "own entities delete" on entities for delete using (auth.uid() = user_id);

-- Tags
create policy "own tags select" on tags for select using (auth.uid() = user_id);
create policy "own tags insert" on tags for insert with check (auth.uid() = user_id);
create policy "own tags update" on tags for update using (auth.uid() = user_id);
create policy "own tags delete" on tags for delete using (auth.uid() = user_id);

-- Junction tables (access via memory ownership check)
create policy "own memory_tags"     on memory_tags     for all using (exists (select 1 from memories where memories.id = memory_tags.memory_id     and memories.user_id = auth.uid()));
create policy "own memory_hashtags" on memory_hashtags for all using (exists (select 1 from memories where memories.id = memory_hashtags.memory_id and memories.user_id = auth.uid()));
create policy "own memory_entities" on memory_entities for all using (exists (select 1 from memories where memories.id = memory_entities.memory_id and memories.user_id = auth.uid()));

-- user settings
create policy "own settings" on user_settings for all using (auth.uid() = user_id);


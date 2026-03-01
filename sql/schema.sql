CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE case_status AS ENUM ('draft', 'active', 'provision_error', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE folder_type AS ENUM ('incoming', 'outgoing', 'evidence');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE deadline_type AS ENUM ('hearing', 'appeal', 'meeting', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE deadline_status AS ENUM ('planned', 'notified', 'expired', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE tg_role AS ENUM ('client', 'lawyer', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE source_channel AS ENUM ('telegram', 'web', 'manual');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE doc_category AS ENUM ('incoming', 'outgoing', 'evidence', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE doc_event_type AS ENUM ('uploaded', 'moved', 'deleted', 'notified', 'error');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE recipient_role AS ENUM ('lawyer', 'client');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE reminder_channel AS ENUM ('telegram', 'email', 'calendar');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE reminder_status AS ENUM ('pending', 'sent', 'error', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref TEXT,
    full_name TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lawyers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT,
    telegram_chat_id BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_code VARCHAR(32) UNIQUE NOT NULL,
    client_id UUID NOT NULL REFERENCES clients(id),
    responsible_lawyer_id UUID NOT NULL REFERENCES lawyers(id),
    case_type VARCHAR(128),
    jurisdiction VARCHAR(128),
    status case_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT case_code_format CHECK (case_code ~ '^C-[0-9]{4}-[0-9]{3}$')
);

CREATE TABLE IF NOT EXISTS case_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    folder_type folder_type NOT NULL,
    storage_provider VARCHAR(32) NOT NULL DEFAULT 'nextcloud',
    folder_path TEXT NOT NULL,
    folder_external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(case_id, folder_type)
);

CREATE TABLE IF NOT EXISTS case_deadlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    deadline_type deadline_type NOT NULL,
    planned_at TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Europe/Moscow',
    notify_lawyer BOOLEAN NOT NULL DEFAULT TRUE,
    notify_client BOOLEAN NOT NULL DEFAULT FALSE,
    status deadline_status NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS telegram_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    telegram_chat_id BIGINT NOT NULL,
    role tg_role NOT NULL,
    client_id UUID REFERENCES clients(id),
    lawyer_id UUID REFERENCES lawyers(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    uploaded_by_telegram_user_id UUID REFERENCES telegram_users(id),
    source_channel source_channel NOT NULL DEFAULT 'telegram',
    doc_category doc_category NOT NULL DEFAULT 'incoming',
    original_filename TEXT,
    stored_filename TEXT NOT NULL,
    mime_type VARCHAR(255),
    size_bytes BIGINT,
    storage_provider VARCHAR(32) NOT NULL DEFAULT 'nextcloud',
    storage_path TEXT NOT NULL,
    storage_file_id TEXT,
    sha256 CHAR(64),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    event_type doc_event_type NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_type deadline_type NOT NULL,
    title_internal TEXT NOT NULL,
    description_internal TEXT,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Europe/Moscow',
    calendar_provider VARCHAR(32) NOT NULL DEFAULT 'yandex360',
    external_event_id TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reminders_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
    recipient_role recipient_role NOT NULL,
    recipient_ref_id UUID NOT NULL,
    channel reminder_channel NOT NULL,
    template_code VARCHAR(64) NOT NULL,
    message_text TEXT NOT NULL,
    send_at TIMESTAMPTZ NOT NULL,
    status reminder_status NOT NULL DEFAULT 'pending',
    retry_count INT NOT NULL DEFAULT 0,
    sent_at TIMESTAMPTZ,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(128) NOT NULL,
    step_name VARCHAR(128),
    severity VARCHAR(16) NOT NULL,
    code VARCHAR(64),
    message TEXT,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

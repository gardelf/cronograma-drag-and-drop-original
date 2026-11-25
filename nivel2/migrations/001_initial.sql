CREATE TABLE IF NOT EXISTS n2_schema_versions(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE n2_values(code text PRIMARY KEY, name text NOT NULL, experiential boolean NOT NULL);
CREATE TABLE n2_units(
 id text PRIMARY KEY, value_code text NOT NULL REFERENCES n2_values(code), name text NOT NULL,
 cost_kind text NOT NULL CHECK(cost_kind IN ('fixed','variable','unknown')),
 standard_cost numeric(14,2) CHECK(standard_cost >= 0),
 satisfaction numeric(4,2) CHECK(satisfaction BETWEEN 0 AND 10),
 hours numeric(10,2) CHECK(hours >= 0), time_note text NOT NULL DEFAULT '',
 version integer NOT NULL DEFAULT 1,
 CHECK(cost_kind <> 'unknown' OR standard_cost IS NULL),
 CHECK(value_code NOT IN ('creativo','responsabilidad') OR (satisfaction IS NULL AND hours IS NULL))
);
CREATE TABLE n2_components(id bigserial PRIMARY KEY, unit_id text NOT NULL REFERENCES n2_units(id), name text NOT NULL, cost numeric(14,2) CHECK(cost>=0));
CREATE TABLE n2_sync_runs(id bigserial PRIMARY KEY, started_at timestamptz DEFAULT now(), finished_at timestamptz, status text NOT NULL, scanned integer DEFAULT 0, error_code text);
CREATE TABLE n2_state(key text PRIMARY KEY, value text NOT NULL);
CREATE TABLE n2_transactions(
 id bigserial PRIMARY KEY, source_instance text NOT NULL, journal_id text NOT NULL, group_id text NOT NULL,
 occurred_on date NOT NULL, description text NOT NULL, amount numeric(14,2) NOT NULL CHECK(amount>=0), currency text NOT NULL,
 financial_category text, merchant text, source_id text, destination_id text, movement_type text NOT NULL,
 fingerprint text NOT NULL, raw jsonb NOT NULL, deleted boolean NOT NULL DEFAULT false,
 eligible boolean NOT NULL, status text NOT NULL CHECK(status IN ('pending','proposed','confirmed','excluded','review')),
 confidence numeric(4,3) NOT NULL DEFAULT 0 CHECK(confidence BETWEEN 0 AND 1), reason text NOT NULL DEFAULT '',
 version integer NOT NULL DEFAULT 1, updated_at timestamptz DEFAULT now(),
 UNIQUE(source_instance,journal_id)
);
CREATE INDEX n2_transactions_date ON n2_transactions(occurred_on,status);
CREATE TABLE n2_allocations(
 id bigserial PRIMARY KEY, transaction_id bigint NOT NULL REFERENCES n2_transactions(id),
 unit_id text NOT NULL REFERENCES n2_units(id), amount numeric(14,2) NOT NULL CHECK(amount>0),
 obligation text NOT NULL CHECK(obligation IN ('obligado','discrecional','desconocido')),
 UNIQUE(transaction_id,unit_id)
);
CREATE TABLE n2_corrections(id bigserial PRIMARY KEY, transaction_id bigint REFERENCES n2_transactions(id), action text NOT NULL, before_data jsonb NOT NULL, after_data jsonb NOT NULL, created_at timestamptz DEFAULT now());
CREATE TABLE n2_rules(signature text PRIMARY KEY, unit_id text NOT NULL REFERENCES n2_units(id), obligation text NOT NULL, confirmations integer NOT NULL DEFAULT 1, updated_at timestamptz DEFAULT now());

-- Archived copy of the former db/init.sql, kept for reference: it is no longer executed.
-- The schema now lives in backend/models/ and backend/migrations/versions/.

-- =====================================================================
-- Schéma de la base + données de référence.
-- Exécuté automatiquement par Postgres au PREMIER démarrage (volume vide).
-- Pour le rejouer : docker compose down -v && docker compose up
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- pour crypt()/gen_salt() (hash bcrypt)

-- ---------------------------------------------------------------------
-- Utilisateurs & rôles
-- ---------------------------------------------------------------------
CREATE TABLE roles (
    id    SERIAL PRIMARY KEY,
    code  VARCHAR(50)  NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    last_name     VARCHAR(100) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE user_roles (
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE audit_logs (
    id            SERIAL PRIMARY KEY,
    actor_user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action        VARCHAR(50)  NOT NULL,
    entity        VARCHAR(100) NOT NULL,
    entity_id     INT,
    payload       JSONB,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Structure pédagogique
-- ---------------------------------------------------------------------
CREATE TABLE academic_years (
    id         SERIAL PRIMARY KEY,
    label      VARCHAR(50) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date   DATE NOT NULL,
    CHECK (end_date > start_date)
);

CREATE TABLE semesters (
    id               SERIAL PRIMARY KEY,
    label            VARCHAR(50) NOT NULL,
    academic_year_id INT NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    start_date       DATE NOT NULL,
    end_date         DATE NOT NULL,
    CHECK (end_date > start_date)
);

CREATE TABLE programs (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(150) NOT NULL,
    level VARCHAR(50)
);

CREATE TABLE subjects (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50)  NOT NULL,
    title       VARCHAR(200) NOT NULL,
    program_id  INT NOT NULL REFERENCES programs(id)  ON DELETE CASCADE,
    semester_id INT NOT NULL REFERENCES semesters(id) ON DELETE RESTRICT,
    UNIQUE (program_id, code)
);

CREATE TABLE session_types (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(20)  NOT NULL UNIQUE,
    label      VARCHAR(100) NOT NULL,
    bg_color   VARCHAR(7)   NOT NULL,
    text_color VARCHAR(7)   NOT NULL
);

CREATE TABLE subject_volumes (
    id              SERIAL PRIMARY KEY,
    subject_id      INT NOT NULL REFERENCES subjects(id)      ON DELETE CASCADE,
    session_type_id INT NOT NULL REFERENCES session_types(id) ON DELETE RESTRICT,
    planned_hours   NUMERIC(6,2) NOT NULL CHECK (planned_hours >= 0),
    UNIQUE (subject_id, session_type_id)
);

CREATE TABLE groups (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    group_type       VARCHAR(20)  NOT NULL,  -- ex : PROMO, TD, TP
    program_id       INT NOT NULL REFERENCES programs(id)       ON DELETE CASCADE,
    academic_year_id INT NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    parent_group_id  INT REFERENCES groups(id) ON DELETE SET NULL
);

CREATE TABLE student_groups (
    user_id  INT NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- ---------------------------------------------------------------------
-- Salles & équipements
-- ---------------------------------------------------------------------
CREATE TABLE rooms (
    id        SERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE,
    capacity  INT NOT NULL CHECK (capacity >= 0),
    room_type VARCHAR(50),
    building  VARCHAR(100),
    floor     VARCHAR(20)
);

CREATE TABLE equipments (
    id    SERIAL PRIMARY KEY,
    label VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE room_equipments (
    room_id      INT NOT NULL REFERENCES rooms(id)      ON DELETE CASCADE,
    equipment_id INT NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
    quantity     INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    PRIMARY KEY (room_id, equipment_id)
);

CREATE TABLE room_unavailabilities (
    id         SERIAL PRIMARY KEY,
    room_id    INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time   TIMESTAMPTZ NOT NULL,
    reason     VARCHAR(255),
    CHECK (end_time > start_time)
);

-- ---------------------------------------------------------------------
-- Séances (emploi du temps)
-- ---------------------------------------------------------------------
CREATE TABLE sessions (
    id                  SERIAL PRIMARY KEY,
    subject_id          INT NOT NULL REFERENCES subjects(id)      ON DELETE CASCADE,
    session_type_id     INT NOT NULL REFERENCES session_types(id) ON DELETE RESTRICT,
    room_id             INT REFERENCES rooms(id) ON DELETE SET NULL,
    start_time          TIMESTAMPTZ NOT NULL,
    end_time            TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'PLANNED',  -- ex : PLANNED, CANCELLED
    comment             TEXT,
    recurrence_group_id UUID,
    CHECK (end_time > start_time)
);

CREATE TABLE session_teachers (
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    teacher_id INT NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (session_id, teacher_id)
);

CREATE TABLE session_groups (
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    group_id   INT NOT NULL REFERENCES groups(id)   ON DELETE CASCADE,
    PRIMARY KEY (session_id, group_id)
);

-- ---------------------------------------------------------------------
-- Disponibilités & préférences
-- ---------------------------------------------------------------------
CREATE TABLE user_unavailabilities (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time   TIMESTAMPTZ NOT NULL,
    reason     VARCHAR(255),
    CHECK (end_time > start_time)
);

CREATE TABLE teacher_preferences (
    id          SERIAL PRIMARY KEY,
    teacher_id  INT NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    subject_id  INT REFERENCES subjects(id)          ON DELETE CASCADE,
    day_of_week SMALLINT CHECK (day_of_week BETWEEN 1 AND 7),  -- 1 = lundi
    time_slot   VARCHAR(20),                                     -- ex : MORNING, AFTERNOON
    priority    SMALLINT NOT NULL DEFAULT 0,
    comment     TEXT
);

-- ---------------------------------------------------------------------
-- Notes, synchro calendrier, notifications
-- ---------------------------------------------------------------------
CREATE TABLE user_session_notes (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, session_id)
);

CREATE TABLE calendar_syncs (
    id           SERIAL PRIMARY KEY,
    user_id      INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider     VARCHAR(50)  NOT NULL,  -- ex : ICS, GOOGLE
    export_token VARCHAR(255) NOT NULL UNIQUE,
    last_sync_at TIMESTAMPTZ
);

CREATE TABLE notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INT REFERENCES sessions(id)       ON DELETE CASCADE,
    type       VARCHAR(50) NOT NULL,             -- ex : SESSION_CHANGED
    channel    VARCHAR(20) NOT NULL,             -- ex : EMAIL, IN_APP
    content    TEXT NOT NULL,
    sent_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at    TIMESTAMPTZ
);

-- =====================================================================
-- Données de référence
-- =====================================================================
INSERT INTO roles (code, label) VALUES
    ('ADMIN',   'Administrateur'),
    ('MANAGER', 'Gestionnaire de scolarité'),
    ('TEACHER', 'Enseignant'),
    ('STUDENT', 'Étudiant');

INSERT INTO session_types (code, label, bg_color, text_color) VALUES
    ('CM',   'Cours magistral',   '#1E3A8A', '#FFFFFF'),
    ('TD',   'Travaux dirigés',   '#047857', '#FFFFFF'),
    ('TP',   'Travaux pratiques', '#B45309', '#FFFFFF'),
    ('EXAM', 'Examen',            '#B91C1C', '#FFFFFF');

-- Compte admin : admin@example.com / admin1234 (hash bcrypt, à changer !)
INSERT INTO users (last_name, first_name, email, password_hash)
VALUES ('Admin', 'Super', 'admin@example.com', crypt('admin1234', gen_salt('bf')));

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'admin@example.com' AND r.code = 'ADMIN';

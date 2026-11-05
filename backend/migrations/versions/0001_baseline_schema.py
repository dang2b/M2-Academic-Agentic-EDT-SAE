"""baseline schema: the former db/init.sql, table for table

Revision ID: 0001
Revises: 
Create Date: 2026-11-05 09:20:33.092827
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Not seen by autogenerate: crypt()/gen_salt() hash passwords in bcrypt (see seed.py)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table('academic_years',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=50), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.CheckConstraint('end_date > start_date', name=op.f('academic_years_check')),
    sa.PrimaryKeyConstraint('id', name=op.f('academic_years_pkey')),
    sa.UniqueConstraint('label', name=op.f('academic_years_label_key'))
    )
    op.create_table('equipments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('equipments_pkey')),
    sa.UniqueConstraint('label', name=op.f('equipments_label_key'))
    )
    op.create_table('programs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('level', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('programs_pkey'))
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('roles_pkey')),
    sa.UniqueConstraint('code', name=op.f('roles_code_key'))
    )
    op.create_table('rooms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('room_type', sa.String(length=50), nullable=True),
    sa.Column('building', sa.String(length=100), nullable=True),
    sa.Column('floor', sa.String(length=20), nullable=True),
    sa.CheckConstraint('capacity >= 0', name=op.f('rooms_capacity_check')),
    sa.PrimaryKeyConstraint('id', name=op.f('rooms_pkey')),
    sa.UniqueConstraint('name', name=op.f('rooms_name_key'))
    )
    op.create_table('session_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=False),
    sa.Column('bg_color', sa.String(length=7), nullable=False),
    sa.Column('text_color', sa.String(length=7), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('session_types_pkey')),
    sa.UniqueConstraint('code', name=op.f('session_types_code_key'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('users_pkey')),
    sa.UniqueConstraint('email', name=op.f('users_email_key'))
    )
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('entity', sa.String(length=100), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('audit_logs_actor_user_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('audit_logs_pkey'))
    )
    op.create_table('calendar_syncs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('export_token', sa.String(length=255), nullable=False),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('calendar_syncs_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('calendar_syncs_pkey')),
    sa.UniqueConstraint('export_token', name=op.f('calendar_syncs_export_token_key'))
    )
    op.create_table('groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('group_type', sa.String(length=20), nullable=False),
    sa.Column('program_id', sa.Integer(), nullable=False),
    sa.Column('academic_year_id', sa.Integer(), nullable=False),
    sa.Column('parent_group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], name=op.f('groups_academic_year_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_group_id'], ['groups.id'], name=op.f('groups_parent_group_id_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], name=op.f('groups_program_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('groups_pkey'))
    )
    op.create_table('room_equipments',
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('room_equipments_quantity_check')),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], name=op.f('room_equipments_equipment_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name=op.f('room_equipments_room_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('room_id', 'equipment_id', name=op.f('room_equipments_pkey'))
    )
    op.create_table('room_unavailabilities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.CheckConstraint('end_time > start_time', name=op.f('room_unavailabilities_check')),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name=op.f('room_unavailabilities_room_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('room_unavailabilities_pkey'))
    )
    op.create_table('semesters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=50), nullable=False),
    sa.Column('academic_year_id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.CheckConstraint('end_date > start_date', name=op.f('semesters_check')),
    sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], name=op.f('semesters_academic_year_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('semesters_pkey'))
    )
    op.create_table('user_roles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('user_roles_role_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_roles_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'role_id', name=op.f('user_roles_pkey'))
    )
    op.create_table('user_unavailabilities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.CheckConstraint('end_time > start_time', name=op.f('user_unavailabilities_check')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_unavailabilities_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('user_unavailabilities_pkey'))
    )
    op.create_table('student_groups',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('student_groups_group_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('student_groups_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'group_id', name=op.f('student_groups_pkey'))
    )
    op.create_table('subjects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('program_id', sa.Integer(), nullable=False),
    sa.Column('semester_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], name=op.f('subjects_program_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('subjects_semester_id_fkey'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('subjects_pkey')),
    sa.UniqueConstraint('program_id', 'code', name=op.f('subjects_program_id_code_key'))
    )
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('session_type_id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.Integer(), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=20), server_default=sa.text("'PLANNED'"), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('recurrence_group_id', sa.Uuid(), nullable=True),
    sa.CheckConstraint('end_time > start_time', name=op.f('sessions_check')),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name=op.f('sessions_room_id_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_type_id'], ['session_types.id'], name=op.f('sessions_session_type_id_fkey'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name=op.f('sessions_subject_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('sessions_pkey'))
    )
    op.create_table('subject_volumes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('session_type_id', sa.Integer(), nullable=False),
    sa.Column('planned_hours', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.CheckConstraint('planned_hours >= 0', name=op.f('subject_volumes_planned_hours_check')),
    sa.ForeignKeyConstraint(['session_type_id'], ['session_types.id'], name=op.f('subject_volumes_session_type_id_fkey'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name=op.f('subject_volumes_subject_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('subject_volumes_pkey')),
    sa.UniqueConstraint('subject_id', 'session_type_id', name=op.f('subject_volumes_subject_id_session_type_id_key'))
    )
    op.create_table('teacher_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('day_of_week', sa.SmallInteger(), nullable=True),
    sa.Column('time_slot', sa.String(length=20), nullable=True),
    sa.Column('priority', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.CheckConstraint('day_of_week BETWEEN 1 AND 7', name=op.f('teacher_preferences_day_of_week_check')),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name=op.f('teacher_preferences_subject_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], name=op.f('teacher_preferences_teacher_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('teacher_preferences_pkey'))
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('channel', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name=op.f('notifications_session_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('notifications_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('notifications_pkey'))
    )
    op.create_table('session_groups',
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('session_groups_group_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name=op.f('session_groups_session_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('session_id', 'group_id', name=op.f('session_groups_pkey'))
    )
    op.create_table('session_teachers',
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.Integer(), nullable=False),
    sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name=op.f('session_teachers_session_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], name=op.f('session_teachers_teacher_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('session_id', 'teacher_id', name=op.f('session_teachers_pkey'))
    )
    op.create_table('user_session_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name=op.f('user_session_notes_session_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_session_notes_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('user_session_notes_pkey')),
    sa.UniqueConstraint('user_id', 'session_id', name=op.f('user_session_notes_user_id_session_id_key'))
    )


def downgrade() -> None:
    op.drop_table('user_session_notes')
    op.drop_table('session_teachers')
    op.drop_table('session_groups')
    op.drop_table('notifications')
    op.drop_table('teacher_preferences')
    op.drop_table('subject_volumes')
    op.drop_table('sessions')
    op.drop_table('subjects')
    op.drop_table('student_groups')
    op.drop_table('user_unavailabilities')
    op.drop_table('user_roles')
    op.drop_table('semesters')
    op.drop_table('room_unavailabilities')
    op.drop_table('room_equipments')
    op.drop_table('groups')
    op.drop_table('calendar_syncs')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('session_types')
    op.drop_table('rooms')
    op.drop_table('roles')
    op.drop_table('programs')
    op.drop_table('equipments')
    op.drop_table('academic_years')
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")

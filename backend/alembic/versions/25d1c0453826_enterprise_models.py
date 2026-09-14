"""enterprise_models

Revision ID: 25d1c0453826
Revises: 
Create Date: 2026-09-14 01:26:06.860258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25d1c0453826'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import uuid

def upgrade() -> None:
    """Upgrade schema."""
    # SQLite often complains about foreign keys when dropping tables in batch mode.
    op.execute("PRAGMA foreign_keys = OFF")

    # Create units table
    op.create_table('units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_units_id'), 'units', ['id'], unique=False)
    op.create_index(op.f('ix_units_name'), 'units', ['name'], unique=True)
    op.create_index(op.f('ix_units_uuid'), 'units', ['uuid'], unique=True)

    # Insert Default Unit
    op.execute(f"INSERT INTO units (uuid, name, description, active) VALUES ('{str(uuid.uuid4())}', 'Unidade Principal', 'Unidade padrão criada durante a migração', 1)")
    
    # Create other tables
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('object_id', sa.String(length=100), nullable=False),
    sa.Column('tenant_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('global_role', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('first_login', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_object_id'), 'users', ['object_id'], unique=True)

    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    
    op.execute("INSERT INTO roles (name, description) VALUES ('ADMIN', 'Administrador da unidade')")
    op.execute("INSERT INTO roles (name, description) VALUES ('TECNICO', 'Técnico da unidade')")
    op.execute("INSERT INTO roles (name, description) VALUES ('VISUALIZACAO', 'Visualização da unidade')")


    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)

    op.create_table('database_metadata',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('application_name', sa.String(length=50), nullable=True),
    sa.Column('database_id', sa.String(length=36), nullable=True),
    sa.Column('organization_id', sa.String(length=36), nullable=True),
    sa.Column('schema_version', sa.Integer(), nullable=True),
    sa.Column('created_by_version', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_metadata_id'), 'database_metadata', ['id'], unique=False)

    op.execute(f"INSERT INTO database_metadata (application_name, database_id, schema_version) VALUES ('NetworkMap', '{str(uuid.uuid4())}', 1)")

    op.create_table('role_permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_permissions_id'), 'role_permissions', ['id'], unique=False)

    op.create_table('user_unit_access',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('unit_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_unit_access_id'), 'user_unit_access', ['id'], unique=False)

    with op.batch_alter_table('racks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_racks_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_racks_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index('ix_racks_name')
        batch_op.create_index(batch_op.f('ix_racks_name'), ['name'], unique=False)
    
    op.execute("UPDATE racks SET unit_id = 1")
    
    # Needs Python logic for UUID, or generate random hex. Sqlite doesn't have native UUID() function easily available
    conn = op.get_bind()
    for row in conn.execute(sa.text("SELECT id FROM racks")).fetchall():
        conn.execute(sa.text(f"UPDATE racks SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('switches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_switches_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_switches_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')

    op.execute("UPDATE switches SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM switches")).fetchall():
        conn.execute(sa.text(f"UPDATE switches SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('locations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_locations_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_locations_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index('ix_locations_name')
        batch_op.create_index(batch_op.f('ix_locations_name'), ['name'], unique=False)

    op.execute("UPDATE locations SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM locations")).fetchall():
        conn.execute(sa.text(f"UPDATE locations SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('vlans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_vlans_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_vlans_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index('ix_vlans_vlan_number')
        batch_op.create_index(batch_op.f('ix_vlans_vlan_number'), ['vlan_number'], unique=False)

    op.execute("UPDATE vlans SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM vlans")).fetchall():
        conn.execute(sa.text(f"UPDATE vlans SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('switch_ports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_switch_ports_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_switch_ports_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')

    op.execute("UPDATE switch_ports SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM switch_ports")).fetchall():
        conn.execute(sa.text(f"UPDATE switch_ports SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_devices_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_devices_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')

    op.execute("UPDATE devices SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM devices")).fetchall():
        conn.execute(sa.text(f"UPDATE devices SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))

    with op.batch_alter_table('connections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_connections_uuid'), ['uuid'], unique=True)
        batch_op.create_foreign_key('fk_connections_units', 'units', ['unit_id'], ['id'], ondelete='CASCADE')
    
    op.execute("UPDATE connections SET unit_id = 1")
    for row in conn.execute(sa.text("SELECT id FROM connections")).fetchall():
        conn.execute(sa.text(f"UPDATE connections SET uuid='{str(uuid.uuid4())}' WHERE id={row[0]}"))
    
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('actor_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('unit_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('hostname', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('ip', sa.String(length=45), nullable=True))
        batch_op.create_foreign_key('fk_audit_logs_users', 'users', ['actor_user_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_audit_logs_units', 'units', ['unit_id'], ['id'], ondelete='SET NULL')

    op.execute("PRAGMA foreign_keys = ON")


def downgrade() -> None:
    """Downgrade schema."""
    pass

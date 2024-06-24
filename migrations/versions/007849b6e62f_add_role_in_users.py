"""add role in users

Revision ID: 007849b6e62f
Revises: 48ebae82d2f8
Create Date: 2024-06-24 10:08:20.635970

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '007849b6e62f'
down_revision = '48ebae82d2f8'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False),)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'role')
    # ### end Alembic commands ###


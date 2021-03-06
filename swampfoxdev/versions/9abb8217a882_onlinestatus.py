"""onlinestatus

Revision ID: 9abb8217a882
Revises: cbcabbea8868
Create Date: 2019-07-02 14:03:02.020249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9abb8217a882'
down_revision = 'cbcabbea8868'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('online', sa.Boolean(), nullable=False, server_default='False'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('player', 'online')
    # ### end Alembic commands ###

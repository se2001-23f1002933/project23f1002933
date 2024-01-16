"""empty message

Revision ID: 19fc48428e36
Revises: 13582e6274a6
Create Date: 2024-01-10 14:30:03.393300

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19fc48428e36'
down_revision = '13582e6274a6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('charges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rentfee', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('member',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=15), nullable=True),
    sa.Column('address', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stock',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=False),
    sa.Column('total_quantity', sa.Integer(), nullable=True),
    sa.Column('available_quantity', sa.Integer(), nullable=True),
    sa.Column('borrowed_quantity', sa.Integer(), nullable=True),
    sa.Column('total_borrowed', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('member_id', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=False),
    sa.Column('issue_date', sa.DateTime(), nullable=False),
    sa.Column('return_date', sa.DateTime(), nullable=True),
    sa.Column('rent_fee', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('student')
    op.drop_table('rent')
    op.drop_table('fee')
    op.drop_column('book', 'Copies')
    op.drop_column('book', 'rented')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('book', sa.Column('rented', sa.INTEGER(), nullable=False))
    op.add_column('book', sa.Column('Copies', sa.INTEGER(), nullable=False))
    op.create_table('fee',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('stu_id', sa.INTEGER(), nullable=False),
    sa.Column('book_id', sa.INTEGER(), nullable=False),
    sa.Column('issue_date', sa.DATETIME(), nullable=False),
    sa.Column('return_date', sa.DATETIME(), nullable=True),
    sa.Column('rent_fee', sa.FLOAT(), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.ForeignKeyConstraint(['stu_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rent',
    sa.Column('rid', sa.INTEGER(), nullable=False),
    sa.Column('book_id', sa.INTEGER(), nullable=False),
    sa.Column('borrowed_quantity', sa.INTEGER(), nullable=True),
    sa.Column('stu_id', sa.INTEGER(), nullable=False),
    sa.Column('date', sa.DATETIME(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.ForeignKeyConstraint(['stu_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('rid')
    )
    op.create_table('student',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('password', sa.VARCHAR(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('transaction')
    op.drop_table('stock')
    op.drop_table('member')
    op.drop_table('charges')
    # ### end Alembic commands ###
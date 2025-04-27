"""add_menu_categories_association

Revision ID: add_menu_categories_association
Revises: 72cd2f329ca7
Create Date: 2025-04-25 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_menu_categories_association'
down_revision: Union[str, None] = '72cd2f329ca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create menu_categories_association table
    op.create_table(
        'menu_categories_association',
        sa.Column('menu_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['menu_id'], ['menus.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['menu_categories.id'], ),
        sa.PrimaryKeyConstraint('menu_id', 'category_id')
    )
    
    # Copy existing category_id relationships to the association table
    op.execute(
        """
        INSERT INTO menu_categories_association (menu_id, category_id)
        SELECT id, category_id FROM menus
        """
    )
    
    # Remove category_id column from menus table
    op.drop_constraint('menus_ibfk_2', 'menus', type_='foreignkey')
    op.drop_column('menus', 'category_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Add category_id column back to menus table
    op.add_column('menus', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key('menus_ibfk_2', 'menus', 'menu_categories', ['category_id'], ['id'])
    
    # Copy the first category for each menu back to the category_id column
    op.execute(
        """
        UPDATE menus m
        SET category_id = (
            SELECT category_id
            FROM menu_categories_association
            WHERE menu_id = m.id
            LIMIT 1
        )
        """
    )
    
    # Make category_id not nullable
    op.alter_column('menus', 'category_id', nullable=False)
    
    # Drop the association table
    op.drop_table('menu_categories_association')
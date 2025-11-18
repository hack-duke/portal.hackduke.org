# SQLAlchemy

**SQLAlchemy** is our Object Relational Mapper (ORM). Instead of managing our database state with SQL commands (i.e. `CREATE TABLE` or `ALTER TABLE`), we define Python classes in models/ that correspond to database tables. SQLAlchemy then handles translating Python into SQL.

**Alembic** is our migration tool. Whenever our models change (new tables, columns, constraints, etc.), Alembic generates migration scripts that update the database schema without wiping existing data.

All of our models live in `models/`. Each file corresponds to a table in our database and contains a class that inherits from a `Base` model. This inheritance is how SQLAlchemy knows our class should be treated as a database table.

## Migrations

Updates to SQLAlchemy models are not applied to the database until an Alembic migration file has been generated and ran.

> You will need a `.env` file with the database credentials to run migrations with Alembic, so if you haven't already, please get this from someone.

Once you are happy with your model changes, run the autogenerate command with a descriptive comment:

```
alembic revision --autogenerate -m "create users table"
```

This will create a file in `alembic/versions/` for your migration. It should look something like this:

```
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "abcd1234efgh"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer, primary_key=True))

def downgrade():
    op.drop_table("users")
```

When you apply an Alembic migration, `upgrade()` is ran. Alembic records the applied revision identifiers (a unique `revision` and its `down_revision`) in a special table (`alembic_version`) so it knows the order of migrations. Together, these identifiers form a directed acyclic graph (DAG) that defines the sequence of schema changes.

If you need to undo a migration, Alembic will call the `downgrade()` function. This should reverse whatever you did in `upgrade()` (for example, dropping a table you created, or removing a column you added).

> ❗ Make sure to read over the migration file and make sure it actually does what you want.
>
> Alembic will autogenerate changes based on differences it detects between your models and the database, so if something was added manually, `upgrade()` will undo that change to re-synchronize the database and ORM state.

To apply your migration to the database, run:

```
alembic upgrade head
```

If you need to roll back one migration, run:

```
alembic downgrade -1
```

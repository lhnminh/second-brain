from alembic import context

from second_brain.config import Settings
from second_brain.db import make_engine, metadata

if context.is_offline_mode():
    context.configure(
        url=Settings().database_url, target_metadata=metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(Settings().database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            render_as_batch=engine.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()

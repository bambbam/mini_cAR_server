from infrastructure.repository import base, model

base.Base.metadata.create_all(base.engine)

"""Mixins for SQLAdmin views to handle dataclass-based models."""

from typing import Any

from starlette.requests import Request


class DataclassModelMixin:
    """Mixin for SQLAdmin ModelView to support dataclass-based SQLAlchemy models.

    SQLAdmin's default insert_model creates an empty model instance via model(),
    then sets attributes. This fails for MappedAsDataclass models with required
    fields that have no defaults.

    This mixin overrides insert_model to create the model WITH the form data,
    which works correctly with dataclass __init__ signatures.

    Usage:
        class MyAdmin(DataclassModelMixin, ModelView, model=MyModel):
            ...

        # For custom data transformation before model creation:
        class UserAdmin(DataclassModelMixin, ModelView, model=User):
            async def on_model_change(self, data, model, is_created, request):
                if is_created:
                    # Transform data BEFORE model is created
                    data["hashed_password"] = hash(data.pop("password"))
    """

    async def insert_model(self, request: Request, data: dict[str, Any]) -> Any:
        """Create model instance with data for dataclass compatibility.

        Instead of creating an empty model then setting attributes,
        we create the model with all data at once, which satisfies
        dataclass required field constraints.
        """
        await self.on_model_change(data, None, True, request)  # type: ignore[attr-defined]

        clean_data = {}
        for key, value in data.items():
            if hasattr(self, "_mapper") and key in self._mapper.relationships:
                rel = self._mapper.relationships[key]
                if rel.direction.name == "MANYTOONE":
                    fk_columns = list(rel.local_columns)
                    if fk_columns:
                        fk_col_name = fk_columns[0].name
                        clean_data[fk_col_name] = int(value) if value else None
                continue

            if value == "" and hasattr(self, "_mapper"):
                col = self._mapper.columns.get(key)
                if col is not None and col.nullable:
                    value = None

            clean_data[key] = value

        obj = self.model(**clean_data)  # type: ignore[attr-defined]

        async with self.session_maker(expire_on_commit=False) as session:  # type: ignore[attr-defined]
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            await self.after_model_change(data, obj, True, request)  # type: ignore[attr-defined]
            return obj

from workout_api.contrib.schemas import BaseSchema
from typing import Annotated
from pydantic import UUID4, BaseModel, Field, PositiveFloat

class Categoria(BaseSchema):
    nome: Annotated[str, Field(description='Nome da categoria', example="Scale", max_length=10)]
    
class CategoriaIn(Categoria):
    pass
    
class CategoriaOut(Categoria):
    id: Annotated[UUID4, Field(description='Identificador da categoria')]
from uuid import uuid4
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Body, status, HTTPException, Query
from pydantic import UUID4
from workout_api.contrib.dependencies import DatabaseDependency
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaAll
from workout_api.atleta.models import AtletaModel
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()
@router.post(
    path='/',
    summary="Criar novo atleta",
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)

async def post(
    db_session: DatabaseDependency,
    atleta_in: AtletaIn = Body()
) -> AtletaOut:
    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=atleta_in.categoria.nome))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Categoria não encontrada com o nome {atleta_in.categoria.nome}'
        )
        
    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=atleta_in.centro_treinamento.nome))
        ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Centro de treinamento não encontrada com o nome {atleta_in.categoria.nome}'
        )

    try:
        try:
            atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
            atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria','centro_treinamento'}))

            atleta_model.categoria_id = categoria.pk_id
            atleta_model.centro_treinamento_id = centro_treinamento.pk_id
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ocorreu um erro ao inserir os dados no banco'
            )

        db_session.add(atleta_model)
        await db_session.commit()

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe atleta com o CPF {atleta_in.cpf}'
        )
    return atleta_out

@router.get(
    path='/',
    summary="Consultar todos os atletas",
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaAll],
)

async def query(db_session: DatabaseDependency) -> Page[AtletaAll]:
    # atletas: list[AtletaAll] = (await db_session.execute(select(AtletaModel))).scalars().all()
    #retorno = [AtletaAll.model_validate(atleta) for atleta in atletas]
    #return paginate(retorno)
    return await paginate(db_session, select(AtletaModel))

@router.get(
    path='/{id}',
    summary="Consultar um atleta por id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)

async def query(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada com o id {id}'
        )
    
    return atleta

@router.get(
    path='/cpf/',
    summary="Consultar um atleta por cpf",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)

async def query(cpf: Annotated[str, Query(max_length=11)], db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(cpf=cpf))
    ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada com o cpf {cpf}'
        )
    return atleta

@router.get(
    path='/nome/',
    summary="Consultar um atleta por nome",
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaOut],
)

async def query(nome: str, db_session: DatabaseDependency) -> Page[AtletaOut]:
    # atleta: AtletaOut = (
    #     await db_session.execute(select(AtletaModel).filter_by(nome=nome))
    # ).scalars().first()
    # 
    # if not atleta:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f'Atleta não encontrada com o nome {nome}'
    #     )
    # return atleta

    return await paginate(db_session, select(AtletaModel).filter(AtletaModel.nome.ilike(f'%{nome}%')))

@router.patch(
    path='/{id}',
    summary="Consultar um atleta por id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)

async def query(id: UUID4, db_session: DatabaseDependency, atleta_up: AtletaUpdate = Body()) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada com o id {id}'
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)
        
    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta

@router.delete(
    path='/{id}',
    summary="Deletar um atleta por id",
    status_code=status.HTTP_204_NO_CONTENT
)

async def query(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada com o id {id}'
        )
    
    await db_session.delete(atleta)
    await db_session.commit()
    return 
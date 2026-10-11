"""Human Rights Agent positions — internal publish, public read.

The agent publishes autonomously (within publication rules: no personal data,
no exact-location inference, no rankings — vitals are per-country absolute
conditions). Positions are append-only; history is public."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import HRAPosition
from ..schemas import HRAPositionIn, HRAPositionOut

router = APIRouter(tags=["hra"])


@router.post("/hra/position", response_model=HRAPositionOut, status_code=201)
async def publish_position(body: HRAPositionIn, session: AsyncSession = Depends(get_session)):
    record = HRAPosition(**body.model_dump())
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/public/hra/position", response_model=HRAPositionOut | None)
async def latest_position(session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(select(HRAPosition).order_by(HRAPosition.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    return row


@router.get("/public/hra/positions", response_model=list[HRAPositionOut])
async def position_history(
    limit: int = Query(default=20, le=100), session: AsyncSession = Depends(get_session)
):
    rows = (
        (await session.execute(
            select(HRAPosition).order_by(HRAPosition.created_at.desc()).limit(limit)
        )).scalars().all()
    )
    return list(rows)

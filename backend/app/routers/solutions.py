"""Solutions engine — internal publish, public read (latest set per country).

Approaches are information_type `recommendation`: machine-drafted options at
political and economic levels, grounded in treated events, labeled as such.
Dispatch to any external party remains a human act."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import SolutionSet
from ..schemas import SolutionSetIn, SolutionSetOut

router = APIRouter(tags=["solutions"])


@router.post("/solutions", response_model=SolutionSetOut, status_code=201)
async def publish_solutions(body: SolutionSetIn, session: AsyncSession = Depends(get_session)):
    record = SolutionSet(**body.model_dump())
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/public/solutions", response_model=list[SolutionSetOut])
async def latest_solutions(session: AsyncSession = Depends(get_session)):
    latest = (
        select(SolutionSet.country, func.max(SolutionSet.created_at).label("mx"))
        .group_by(SolutionSet.country).subquery()
    )
    rows = (
        (await session.execute(
            select(SolutionSet).join(
                latest, (SolutionSet.country == latest.c.country)
                & (SolutionSet.created_at == latest.c.mx)
            ).order_by(SolutionSet.created_at.desc())
        )).scalars().all()
    )
    return list(rows)


@router.get("/public/solutions/history", response_model=list[SolutionSetOut])
async def solutions_history(
    country: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    session: AsyncSession = Depends(get_session),
):
    q = select(SolutionSet).order_by(SolutionSet.created_at.desc()).limit(limit)
    if country:
        q = q.where(SolutionSet.country == country.upper())
    rows = (await session.execute(q)).scalars().all()
    return list(rows)

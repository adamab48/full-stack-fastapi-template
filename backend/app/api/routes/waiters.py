from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Waiter,
    WaiterCreate,
    WaiterOut,
    WaitersOut,
    WaiterUpdate,
    Message,
)

router = APIRouter()


@router.get("/", response_model=WaitersOut)
def read_waiters(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve waiters.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Waiter)
        count = session.exec(count_statement).one()
        statement = select(Waiter).offset(skip).limit(limit)
        waiters = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Waiter)
            .where(Waiter.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Waiter)
            .where(Waiter.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        waiters = session.exec(statement).all()

    return WaitersOut(data=waiters, count=count)


@router.get("/{id}", response_model=WaiterOut)
def read_waiter(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get waiter by ID.
    """
    waiter = session.get(Waiter, id)
    if not waiter:
        raise HTTPException(status_code=404, detail="Waiter not found")
    if not current_user.is_superuser and (waiter.id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return waiter


@router.post("/", response_model=WaiterOut)
def create_waiter(
    *, session: SessionDep, current_user: CurrentUser, waiter_in: WaiterCreate
) -> Any:
    """
    Create new waiter.
    """
    print(waiter_in)
    return waiter_in
    waiter = Waiter.model_validate(waiter_in, update={"owner_id": current_user.id})
    session.add(waiter)
    session.commit()
    session.refresh(waiter)
    return waiter


@router.put("/{id}", response_model=WaiterOut)
def update_waiter(
    *, session: SessionDep, current_user: CurrentUser, id: int, waiter_in: WaiterUpdate
) -> Any:
    """
    Update an waiter.
    """
    waiter = session.get(Waiter, id)
    if not waiter:
        raise HTTPException(status_code=404, detail="Waiter not found")
    if not current_user.is_superuser and (waiter.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = waiter_in.model_dump(exclude_unset=True)
    waiter.sqlmodel_update(update_dict)
    session.add(waiter)
    session.commit()
    session.refresh(waiter)
    return waiter


@router.delete("/{id}")
def delete_waiter(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    """
    Delete an waiter.
    """
    waiter = session.get(Waiter, id)
    if not waiter:
        raise HTTPException(status_code=404, detail="Waiter not found")
    if not current_user.is_superuser and (waiter.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(waiter)
    session.commit()
    return Message(message="Waiter deleted successfully")

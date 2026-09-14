from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, require_any_management
)
from app.models import User as UserModel, UserRole
from app.schemas import UserCreate, User as UserSchema, Token, LoginRequest, UserRole as SchemaUserRole

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_any_management)
):
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    user = UserModel(
        name=user_data.name,
        role=user_data.role,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user


@router.get("/users", response_model=list[UserSchema])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_any_management)
):
    result = await db.execute(select(UserModel))
    return result.scalars().all()


@router.get("/roles", response_model=list[str])
async def get_roles():
    return [role.value for role in UserRole]
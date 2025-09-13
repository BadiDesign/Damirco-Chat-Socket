from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.database import get_db
from users.schemas import *
from users.models import UserModel

router = APIRouter(tags=["users"])

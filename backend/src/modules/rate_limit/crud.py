from fastcrud import FastCRUD

from .models import RateLimit

crud_rate_limits: FastCRUD = FastCRUD(RateLimit)

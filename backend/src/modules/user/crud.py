from fastcrud import FastCRUD

from .models import User

crud_users: FastCRUD = FastCRUD(User)

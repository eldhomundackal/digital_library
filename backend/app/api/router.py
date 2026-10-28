"""Central API router — wires all v1 routers."""

from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1 import authors
from app.api.v1 import books
from app.api.v1 import categories
from app.api.v1 import kyc
from app.api.v1 import publisher_books
from app.api.v1 import publishers
from app.api.v1 import tags
from app.api.v1 import users
from app.api.v1 import utils
from app.api.v1 import reviews
from app.api.v1.admin import activity as admin_activity
from app.api.v1.admin import analytics as admin_analytics
from app.api.v1.admin import authors as admin_authors
from app.api.v1.admin import books as admin_books
from app.api.v1.admin import categories as admin_categories
from app.api.v1.admin import kyc as admin_kyc
from app.api.v1.admin import notifications as admin_notifications
from app.api.v1.admin import reviews as admin_reviews
from app.api.v1.admin import tags as admin_tags
from app.api.v1.admin import users as admin_users
from app.api.v1.admin import utils as admin_utils

api_router = APIRouter()

# Auth
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# User & profile
api_router.include_router(users.router)
api_router.include_router(kyc.router)

# Publisher public pages
api_router.include_router(publishers.router)
api_router.include_router(publisher_books.router)

# Books public
api_router.include_router(books.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
api_router.include_router(authors.router)
api_router.include_router(reviews.router)

# Public utilities
api_router.include_router(utils.router)

# Admin routers
api_router.include_router(admin_kyc.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_utils.router)
api_router.include_router(admin_books.router)
api_router.include_router(admin_tags.router)
api_router.include_router(admin_categories.router)
api_router.include_router(admin_authors.router)
api_router.include_router(admin_reviews.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_activity.router)
api_router.include_router(admin_notifications.router)

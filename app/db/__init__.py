# This empty file tells Python to treat the 'models' directory as a package.
# Without this, importing 'app.db.models.user' will fail.
# It resolves the "is not a package" error we had previously.
# /home/angel/repos/helixnet/app/db/__init__.py
# We can optionally import all models here to make them easier to access from one place.

# from .task_model import TaskResult # Assuming TaskResult will be moved here later
# This empty file tells Python to treat the 'models' directory as a package.
# It resolves the "is not a package" error we had previously.

# IMPORTANT: We are removing the explicit import here to avoid a "Table already defined" error
# caused by double-loading the model during application startup.
# Other modules should now import models directly from their respective files (e.g., from app.db.models.user import User).

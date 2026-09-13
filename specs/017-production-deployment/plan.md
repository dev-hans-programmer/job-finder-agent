# Implementation plan

1. Add a production Compose override with isolated volumes, private infrastructure ports, and required secrets.
2. Add production smoke tests and deployment/rollback scripts.
3. Record the current image and tag after a successful deployment.
4. Back up the database and run migrations before starting the new application image.
5. Automatically roll back the application image if post-deployment checks fail.
6. Add manually approved GitHub Actions workflows for deployment and rollback.
7. Document expand-and-contract migration requirements and explicit database restore recovery.
8. Validate shell scripts, Compose interpolation, workflow configuration, lint, tests, and coverage.

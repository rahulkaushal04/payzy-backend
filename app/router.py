from app.controller.auth_controller import auth_router


routes = [{"router": auth_router, "prefix": "/auth", "tags": ["authentication"]}]

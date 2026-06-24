(venv) [thobbs@EastManAndro Backend]$ uvicorn app.main:app --reload
INFO:     Will watch for changes in these directories: ['/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [58919] using WatchFiles
INFO:     Started server process [58923]
INFO:     Waiting for application startup.
============================================================
🚀 Majiscope Backend v1.0.0 Starting...
   Environment: development
   Backend URL: http://0.0.0.0:8000
   Frontend URL: http://localhost:3000
============================================================
INFO:     Application startup complete.
2026-03-05 18:38:34,576 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:38:34,645 INFO sqlalchemy.engine.Engine select pg_catalog.version()
2026-03-05 18:38:34,645 - sqlalchemy.engine.Engine - INFO - select pg_catalog.version()
2026-03-05 18:38:34,646 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-03-05 18:38:34,646 - sqlalchemy.engine.Engine - INFO - [raw sql] {}
2026-03-05 18:38:34,648 INFO sqlalchemy.engine.Engine select current_schema()
2026-03-05 18:38:34,648 - sqlalchemy.engine.Engine - INFO - select current_schema()
2026-03-05 18:38:34,648 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-03-05 18:38:34,648 - sqlalchemy.engine.Engine - INFO - [raw sql] {}
2026-03-05 18:38:34,650 INFO sqlalchemy.engine.Engine show standard_conforming_strings
2026-03-05 18:38:34,650 - sqlalchemy.engine.Engine - INFO - show standard_conforming_strings
2026-03-05 18:38:34,650 INFO sqlalchemy.engine.Engine [raw sql] {}
2026-03-05 18:38:34,650 - sqlalchemy.engine.Engine - INFO - [raw sql] {}
2026-03-05 18:38:34,651 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:38:34,651 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:38:34,655 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:34,655 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:34,655 INFO sqlalchemy.engine.Engine [generated in 0.00029s] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:34,655 - sqlalchemy.engine.Engine - INFO - [generated in 0.00029s] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:34,875 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:38:34,875 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:38:34,877 - app.middleware.exception_handlers - ERROR - Unhandled Exception: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
INFO:     127.0.0.1:36368 - "POST /api/auth/login HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 426, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/applications.py", line 1106, in __call__
    await super().__call__(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc283716660>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
2026-03-05 18:38:35,911 - app.middleware.logging - INFO - → OPTIONS /api/auth/login
2026-03-05 18:38:35,914 - app.middleware.logging - INFO - ← OPTIONS /api/auth/login - 200
INFO:     127.0.0.1:36380 - "OPTIONS /api/auth/login HTTP/1.1" 200 OK
2026-03-05 18:38:35,918 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:38:35,920 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:38:35,920 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:38:35,921 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:35,921 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:35,921 INFO sqlalchemy.engine.Engine [cached since 1.266s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:35,921 - sqlalchemy.engine.Engine - INFO - [cached since 1.266s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:36,135 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:38:36,135 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:38:36,136 - app.middleware.exception_handlers - ERROR - Unhandled Exception: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
INFO:     127.0.0.1:36380 - "POST /api/auth/login HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 426, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/applications.py", line 1106, in __call__
    await super().__call__(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236c050>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
2026-03-05 18:38:38,216 - app.middleware.logging - INFO - → OPTIONS /api/auth/login
2026-03-05 18:38:38,217 - app.middleware.logging - INFO - ← OPTIONS /api/auth/login - 200
INFO:     127.0.0.1:41148 - "OPTIONS /api/auth/login HTTP/1.1" 200 OK
2026-03-05 18:38:38,219 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:38:38,222 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:38:38,222 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:38:38,222 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:38,222 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:38,222 INFO sqlalchemy.engine.Engine [cached since 3.567s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:38,222 - sqlalchemy.engine.Engine - INFO - [cached since 3.567s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:38,434 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:38:38,434 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:38:38,434 - app.middleware.exception_handlers - ERROR - Unhandled Exception: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
INFO:     127.0.0.1:41148 - "POST /api/auth/login HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 426, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/applications.py", line 1106, in __call__
    await super().__call__(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc2823584a0>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
2026-03-05 18:38:42,455 - app.middleware.logging - INFO - → OPTIONS /api/auth/login
2026-03-05 18:38:42,456 - app.middleware.logging - INFO - ← OPTIONS /api/auth/login - 200
INFO:     127.0.0.1:41162 - "OPTIONS /api/auth/login HTTP/1.1" 200 OK
2026-03-05 18:38:42,459 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:38:42,461 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:38:42,461 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:38:42,461 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:42,461 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:38:42,461 INFO sqlalchemy.engine.Engine [cached since 7.806s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:42,461 - sqlalchemy.engine.Engine - INFO - [cached since 7.806s ago] {'email_1': 'admin@majiscope.com', 'param_1': 1}
2026-03-05 18:38:42,673 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:38:42,673 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:38:42,674 - app.middleware.exception_handlers - ERROR - Unhandled Exception: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
INFO:     127.0.0.1:41162 - "POST /api/auth/login HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock
anyio.WouldBlock

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 78, in call_next
    message = await recv_stream.receive()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream
anyio.EndOfStream

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 426, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/applications.py", line 1106, in __call__
    await super().__call__(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 37, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/logging.py", line 73, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 108, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/middleware/rate_limiting.py", line 67, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 84, in call_next
    raise app_exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 70, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 91, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 146, in simple_response
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 20, in __call__
    raise e
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 17, in __call__
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/starlette/routing.py", line 66, in app
    response = await func(request)
               ^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 274, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/app/api/auth.py", line 119, in login
    user=UserResponse.from_orm(user),
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 1475, in from_orm
    return cls.model_validate(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/run/media/thobbs/EastManPhoenyXP/MAJISCOPE/Majiscope/Backend/venv/lib/python3.12/site-packages/pydantic/main.py", line 716, in model_validate
    return cls.__pydantic_validator__.validate_python(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserResponse
first_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
last_name
  Field required [type=missing, input_value=<app.models.user.User object at 0x7fc28236fe90>, input_type=User]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
2026-03-05 18:39:08,036 - app.middleware.logging - INFO - → OPTIONS /api/auth/login
2026-03-05 18:39:08,038 - app.middleware.logging - INFO - ← OPTIONS /api/auth/login - 200
INFO:     127.0.0.1:48406 - "OPTIONS /api/auth/login HTTP/1.1" 200 OK
2026-03-05 18:39:08,055 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:39:08,058 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:39:08,058 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:39:08,059 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:08,059 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:08,059 INFO sqlalchemy.engine.Engine [cached since 33.4s ago] {'email_1': 'manager@dawasa.go.tz', 'param_1': 1}
2026-03-05 18:39:08,059 - sqlalchemy.engine.Engine - INFO - [cached since 33.4s ago] {'email_1': 'manager@dawasa.go.tz', 'param_1': 1}
2026-03-05 18:39:08,060 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:39:08,060 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:39:08,061 - app.middleware.logging - INFO - ← POST /api/auth/login - 401
INFO:     127.0.0.1:48406 - "POST /api/auth/login HTTP/1.1" 401 Unauthorized
2026-03-05 18:39:16,348 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:39:16,351 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:39:16,351 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:39:16,351 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:16,351 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:16,351 INFO sqlalchemy.engine.Engine [cached since 41.7s ago] {'email_1': 'dp33@gmail.com', 'param_1': 1}
2026-03-05 18:39:16,351 - sqlalchemy.engine.Engine - INFO - [cached since 41.7s ago] {'email_1': 'dp33@gmail.com', 'param_1': 1}
2026-03-05 18:39:16,352 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:39:16,352 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:39:16,353 - app.middleware.logging - INFO - ← POST /api/auth/login - 401
INFO:     127.0.0.1:48408 - "POST /api/auth/login HTTP/1.1" 401 Unauthorized
2026-03-05 18:39:26,640 - app.middleware.logging - INFO - → POST /api/auth/login
2026-03-05 18:39:26,643 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-05 18:39:26,643 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)
2026-03-05 18:39:26,643 INFO sqlalchemy.engine.Engine SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:26,643 - sqlalchemy.engine.Engine - INFO - SELECT "user".id AS user_id, "user".email AS user_email, "user".password AS user_password, "user".name AS user_name, "user".phone AS user_phone, "user".avatar AS user_avatar, "user".status AS user_status, "user".created_at AS user_created_at, "user".updated_at AS user_updated_at 
FROM "user" 
WHERE "user".email = %(email_1)s 
 LIMIT %(param_1)s
2026-03-05 18:39:26,643 INFO sqlalchemy.engine.Engine [cached since 51.99s ago] {'email_1': 'dpma33@gmail.com', 'param_1': 1}
2026-03-05 18:39:26,643 - sqlalchemy.engine.Engine - INFO - [cached since 51.99s ago] {'email_1': 'dpma33@gmail.com', 'param_1': 1}
2026-03-05 18:39:26,645 INFO sqlalchemy.engine.Engine ROLLBACK
2026-03-05 18:39:26,645 - sqlalchemy.engine.Engine - INFO - ROLLBACK
2026-03-05 18:39:26,646 - app.middleware.logging - INFO - ← POST /api/auth/login - 401
INFO:     127.0.0.1:39990 - "POST /api/auth/login HTTP/1.1" 401 Unauthorized

, we need to make sure that the login logic checks three tables for login, utility managers,DMA managers,engineers (here the role is checked if engineer or team leader on this engineers table), and users table(this is mostly used by admins) so we need to make the logic work as it was working previously 
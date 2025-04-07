# Chapter 1: Main Application Structure

## Introduction

The main application structure in FastAPI is designed to be simple yet powerful. It provides a clean way to define your API endpoints, middleware, and dependencies. In this chapter, we'll explore how FastAPI applications are structured and how the core components work together.

## FastAPI Class

The `FastAPI` class is the main entry point for creating a FastAPI application. It inherits from Starlette's `Starlette` class and adds additional functionality specific to API development.

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="This is a sample API",
    version="0.1.0"
)
```

The `FastAPI` class accepts various parameters to customize your application:

- `title`: The title of your API, used in the OpenAPI documentation
- `description`: A description of your API, used in the OpenAPI documentation
- `version`: The version of your API
- `openapi_url`: The URL where the OpenAPI schema will be served (default: `/openapi.json`)
- `docs_url`: The URL for the Swagger UI documentation (default: `/docs`)
- `redoc_url`: The URL for the ReDoc documentation (default: `/redoc`)
- `dependencies`: A list of dependencies that will be applied to all routes
- `middleware`: A list of middleware to be added to the application

## Route Definitions

Routes in FastAPI are defined using decorators. The most common decorators are:

- `@app.get()`: For HTTP GET requests
- `@app.post()`: For HTTP POST requests
- `@app.put()`: For HTTP PUT requests
- `@app.delete()`: For HTTP DELETE requests
- `@app.patch()`: For HTTP PATCH requests
- `@app.options()`: For HTTP OPTIONS requests
- `@app.head()`: For HTTP HEAD requests

Here's an example of defining routes:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: Item):
    return item
```

## Application Lifecycle Events

FastAPI provides hooks for application startup and shutdown events:

```python
@app.on_event("startup")
async def startup_event():
    # Code to run on application startup
    print("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    # Code to run on application shutdown
    print("Application shutdown")
```

These events are useful for initializing resources (like database connections) on startup and cleaning them up on shutdown.

## Application Structure for Larger Projects

For larger projects, it's common to organize the code into multiple modules:

```
my_fastapi_app/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application creation and configuration
│   ├── dependencies.py  # Shared dependencies
│   ├── routers/         # Route modules
│   │   ├── __init__.py
│   │   ├── items.py
│   │   └── users.py
│   ├── models/          # Pydantic models
│   │   ├── __init__.py
│   │   ├── item.py
│   │   └── user.py
│   ├── crud/            # Database operations
│   │   ├── __init__.py
│   │   ├── item.py
│   │   └── user.py
│   └── db/              # Database configuration
│       ├── __init__.py
│       └── database.py
└── tests/               # Tests
    ├── __init__.py
    ├── test_items.py
    └── test_users.py
```

In this structure:

- `main.py` creates and configures the FastAPI application
- `dependencies.py` contains shared dependencies
- `routers/` contains route modules, which are included in the main application
- `models/` contains Pydantic models for request and response validation
- `crud/` contains database operations
- `db/` contains database configuration
- `tests/` contains tests for the application

## Including Routers

For larger applications, you can split your routes into multiple files using `APIRouter`:

```python
# app/routers/items.py
from fastapi import APIRouter, Depends, HTTPException
from .. import dependencies

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(dependencies.get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_items():
    return [{"name": "Item 1"}, {"name": "Item 2"}]

@router.get("/{item_id}")
async def read_item(item_id: str):
    return {"name": "Item", "item_id": item_id}
```

Then include the router in your main application:

```python
# app/main.py
from fastapi import FastAPI
from .routers import items, users

app = FastAPI()

app.include_router(items.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Conclusion

The main application structure in FastAPI is designed to be flexible and scalable. It provides a clean way to define your API endpoints, middleware, and dependencies. By organizing your code into modules, you can keep your application maintainable as it grows.

In the next chapter, we'll dive deeper into the routing system and how it handles different types of requests.

---

**Next Chapter**: [Routing System](chapter_2_routing.md)

**Previous Chapter**: None

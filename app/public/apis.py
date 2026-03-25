from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
def hello():
    return {"message": "Hello World"}

@router.get("/health")
def health_check():
    return {"status": "healthy"}
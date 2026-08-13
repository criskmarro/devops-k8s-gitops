import models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DevOps K8s GitOps API",
    description="Cloud-native API deployed on Kubernetes with GitOps",
    version="1.0.0"
)

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemResponse(ItemCreate):
    id: int
    class Config:
        from_attributes = True

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "devops-k8s-gitops"}

@app.get("/items", response_model=list[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()

@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
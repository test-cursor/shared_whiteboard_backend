from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Point(BaseModel):
    x: float
    y: float

class Path(BaseModel):
    points: List[Point]
    stroke_width: float
    color: str
    timestamp: datetime

class DrawingData(BaseModel):
    paths: List[Path]
    room_id: str

class SVGExport(BaseModel):
    svg_content: str
    filename: str
    timestamp: datetime

class DrawingImport(BaseModel):
    svg_content: str
    room_id: str

class BatchedDrawingActions(BaseModel):
    actions: List[Path]
    room_id: str
    timestamp: datetime
    batch_id: str  # For conflict resolution 
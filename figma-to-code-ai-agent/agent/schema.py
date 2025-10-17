from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

NodeType = Literal["FRAME","TEXT","RECTANGLE","ELLIPSE","IMAGE","INSTANCE","GROUP"]

class Bounds(BaseModel):
    x: float
    y: float
    width: float
    height: float

class Color(BaseModel):
    r: float
    g: float
    b: float
    a: float = 1.0

class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    font_weight: Optional[int] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[float] = None
    text_align: Optional[str] = None

class Node(BaseModel):
    id: str
    name: str
    type: NodeType
    bounds: Optional[Bounds] = None
    fill: Optional[Color] = None
    stroke: Optional[Color] = None
    text: Optional[str] = None
    text_style: Optional[TextStyle] = None
    children: List["Node"] = Field(default_factory=list)

class UISchema(BaseModel):
    file_name: str = "Untitled"
    root_frames: List[Node] = Field(default_factory=list)
    tokens: Dict[str, Any] = Field(default_factory=dict)

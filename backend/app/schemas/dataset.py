from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

ColumnDataType = Literal['numeric', 'categorical', 'datetime', 'boolean', 'text', 'id']
FileType = Literal['csv', 'xls', 'xlsx']
DatasetStatus = Literal['uploaded', 'processing', 'completed', 'failed']

class CategoryCount(BaseModel):
    label: str
    count: int
    percentage: float

class HistogramBucket(BaseModel):
    bucket: str
    count: int

class DatasetColumnSummary(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    stdDev: Optional[float] = None
    uniqueCount: int = 0
    nullCount: int = 0
    totalCount: int = 0
    topCategories: Optional[List[CategoryCount]] = None
    distribution: Optional[List[HistogramBucket]] = None

class DatasetColumn(BaseModel):
    name: str
    key: str
    originalName: str
    dataType: ColumnDataType
    summary: Optional[DatasetColumnSummary] = None
    description: Optional[str] = None
    isTarget: Optional[bool] = False

class Dataset(BaseModel):
    id: str
    projectId: str
    name: str
    description: Optional[str] = ""
    rowCount: int = 0
    columnCount: int = 0
    columns: List[DatasetColumn] = Field(default_factory=list)
    sampleRows: List[Dict[str, Any]] = Field(default_factory=list)
    sizeBytes: int = 0
    uploadedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fileType: FileType = "csv"
    fileName: Optional[str] = None
    storageBucket: Optional[str] = "datasets"
    storagePath: Optional[str] = None
    status: DatasetStatus = "completed"
    errorMessage: Optional[str] = None
    processingTimeMs: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

class DatasetPreviewResponse(BaseModel):
    id: str
    projectId: str
    name: str
    status: DatasetStatus
    rowCount: int
    columnCount: int
    columns: List[DatasetColumn]
    sampleRows: List[Dict[str, Any]]
    fileType: FileType
    storagePath: Optional[str] = None
    errorMessage: Optional[str] = None
    processingTimeMs: Optional[float] = None

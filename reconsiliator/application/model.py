from pydantic import BaseModel, HttpUrl

class Source(BaseModel):
    urlPath: HttpUrl
    subPath: str
    targetRevision: str

class Metadata(BaseModel):
    name: str

class Spec(BaseModel):
    source: Source

class Application(BaseModel):
    apiVersion: str
    kind: str
    metadata: Metadata
    spec: Spec
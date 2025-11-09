"""FastAPI server for Text to Process Model transformation."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from agents.orchestrator_agent import OrchestratorAgent
from utils.file_handler import ensure_output_dir


# Initialize FastAPI app
app = FastAPI(
    title="Text to Process Model API",
    description="Transform natural language process descriptions into BPMN 2.0 models",
    version="1.0.0",
)


class ProcessTransformRequest(BaseModel):
    """Request model for process transformation."""
    process_description: str = Field(..., min_length=10)
    process_name: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None


@app.get("/")
async def root():
    """API health check."""
    return {
        "name": "Text to Process Model API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/transform")
async def transform_process(request: ProcessTransformRequest):
    """Transform a process description into BPMN 2.0."""
    try:
        if len(request.process_description) < 20:
            raise HTTPException(
                status_code=400,
                detail="Process description must be at least 20 characters",
            )

        deep_agent = OrchestratorAgent(api_key=request.api_key)
        result = deep_agent.run_complete_workflow(
            process_description=request.process_description,
            process_name=request.process_name,
        )

        return {
            "status": result["status"],
            "process_name": request.process_name,
            "parser_status": result["parser"]["status"],
            "modeler_status": result["modeler"]["status"],
            "output_folders": {
                "parser": result["parser"]["output_folder"],
                "modeler": result["modeler"]["output_folder"],
            },
            "files": {
                "parser": result["parser"]["files_saved"],
                "modeler": result["modeler"]["files_saved"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
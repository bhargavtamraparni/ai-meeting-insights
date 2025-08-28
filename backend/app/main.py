import os, sys
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import schemas
from .database import db_manager, Base
from .crud import meeting_crud
from .ai_processing import AIPipeline, VectorStoreService

class AppCreator:
    """
    A class to create and configure the FastAPI application, encapsulating all
    setup logic and routing.
    """

    def __init__(self):
        # --- App Initialization and Configuration ---
        self.app = FastAPI(title="AI Meeting Intelligence Platform")

        # --- Initialize Services/Managers ---
        self.ai_pipeline = AIPipeline(db_session_factory=db_manager.SessionLocal)

        # --- Run Startup Tasks ---
        self._create_db_tables()
        self._configure_middleware()
        self._create_upload_dir()

        # --- Register API Routes ---
        self._register_routes()

    def _create_db_tables(self):
        """Creates database tables if they don't exist."""
        Base.metadata.create_all(bind=db_manager.engine)

    def _configure_middleware(self):
        """Sets up CORS middleware for the application."""
        self.app.add_middleware(
            CORSMiddleware,
            # allow_origins=["http://localhost:3000"],
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _create_upload_dir(self):
        """Ensures the upload directory exists."""
        os.makedirs("uploads", exist_ok=True)

    def _register_routes(self):
        """Defines and registers all API endpoints for the application."""

        @self.app.post("/upload", response_model=schemas.MeetingStatus, status_code=202)
        async def upload_file(
                background_tasks: BackgroundTasks,
                file: UploadFile = File(...),
                db: Session = Depends(db_manager.get_db)
        ):
            print("UPLOAD FILE HIT", file.filename, file.content_type)
            if not file.content_type.startswith(("audio/", "video/")):
                raise HTTPException(status_code=400, detail="Invalid file type.")

            file_path = os.path.join("uploads", f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}")
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            meeting = meeting_crud.create(db=db, filename=file.filename)

            # Use the pipeline instance from the class
            background_tasks.add_task(self.ai_pipeline.run, meeting_id=meeting.id, filepath=file_path)

            return {"id": meeting.id, "status": meeting.status, "filename": meeting.filename}

        @self.app.get("/meetings", response_model=list[schemas.Meeting])
        def get_all_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(db_manager.get_db)):
            return meeting_crud.get_multi(db, skip=skip, limit=limit)

        @self.app.get("/meetings/{meeting_id}", response_model=schemas.Meeting)
        def get_meeting_details(meeting_id: int, db: Session = Depends(db_manager.get_db)):
            db_meeting = meeting_crud.get(db, meeting_id=meeting_id)
            if db_meeting is None:
                raise HTTPException(status_code=404, detail="Meeting not found")
            return db_meeting

        @self.app.get("/meetings/{meeting_id}/status", response_model=schemas.MeetingStatus)
        def get_meeting_status(meeting_id: int, db: Session = Depends(db_manager.get_db)):
            db_meeting = meeting_crud.get(db, meeting_id=meeting_id)
            if db_meeting is None:
                raise HTTPException(status_code=404, detail="Meeting not found")
            return {"id": db_meeting.id, "status": db_meeting.status, "filename": db_meeting.filename}

        @self.app.post("/search/{meeting_id}", response_model=schemas.SearchResult)
        def search_in_meeting(meeting_id: int, query: schemas.SearchQuery, db: Session = Depends(db_manager.get_db)):
            db_meeting = meeting_crud.get(db, meeting_id)
            if not db_meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")
            if db_meeting.status != "completed":
                raise HTTPException(status_code=400, detail="Meeting is still processing.")

            # Use the vector_store from the pipeline instance
            answer = self.ai_pipeline.vector_store.search(meeting_id, query.query)
            return {"answer": answer}

        @self.app.get("/", include_in_schema=False)
        def root():
            return {"message": "AI Meeting Intelligence API is running. See /docs for documentation."}


# --- Global Application Instance ---
# Uvicorn will look for this 'app' variable.
creator = AppCreator()
app = creator.app
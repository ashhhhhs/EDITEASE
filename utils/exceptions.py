class EditEaseError(Exception):
    """Base exception for all EditEase custom errors."""
    pass

class VideoProcessingError(EditEaseError):
    """Raised when the video processing pipeline (FFmpeg, OpenCV) fails."""
    pass

class ConfigurationError(EditEaseError):
    """Raised when a critical configuration setting is missing or invalid."""
    pass

class DatabaseError(EditEaseError):
    """Raised for MongoDB connection or query failures."""
    pass

class SceneExtractionError(EditEaseError):
    """Raised when scene boundary detection fails."""
    pass

class EmotionDetectionError(EditEaseError):
    """Raised when deepface emotion analysis fails on a frame."""
    pass

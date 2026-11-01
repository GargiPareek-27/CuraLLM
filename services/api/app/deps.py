"""FastAPI dependencies."""
from fastapi import Request

from app.inference_client import InferenceClient


def get_inference_client(request: Request) -> InferenceClient:
    return request.app.state.inference_client

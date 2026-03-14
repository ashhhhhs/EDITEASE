from setuptools import setup, find_packages

setup(
    name="editease",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "pymongo",
        "streamlit",
        "opencv-python",
        "requests",
        "numpy",
        "scenedetect",
        "deepface",
        "celery",
        "redis",
        "flasgger"
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"]
    }
)

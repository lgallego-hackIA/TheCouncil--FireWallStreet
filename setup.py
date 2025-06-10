from setuptools import setup, find_packages

setup(
    name="geopark-automation",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "requests",
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "geopark-server=src.api.data_endpoints:app"
        ]
    }
) 
# FastAPI Pocketbase Handler

## Overview

This is a FastAPI application designed to serve as a handler for a Pocketbase app.

## Features

- FastAPI-based RESTful API
- Integration with Pocketbase for seamless data handling
- Form-filling endpoints for user software applications

## Requirements

- Python 3.9.13
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

```bash
git clone [repository-url]

2. Navigate to the project directory:
cd fastapi-pocketbase-handler

3. Create a virtual environment (recommended):
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

4. Install dependencies:
pip install -r requirements.txt

## Running the Application
1. Navigate to the project directory:
cd fastapi-pocketbase-handler

2. Activate the virtual environment:
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Run the development server:
uvicorn main:app --reload

4. For production (without reloading, optimized settings):
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

## Configure the Environmental Variables
POCKETBASE_URL=http://your-pocketbase-instance:8090
```

# Audio QA Frontend

React frontend for the Audio Quality Assurance application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## API Server

Make sure the Flask API server is running. Start it with:

```bash
python src/api_server.py
```

The API server runs on `http://localhost:5000` by default.

## Environment Variables

You can set the API URL by creating a `.env` file:

```
REACT_APP_API_URL=http://localhost:5000/api
```

## Features

- **Gallery View**: Browse all processed audio files
- **Queue Progress**: Real-time queue status monitoring
- **File Upload**: Upload audio files for processing
- **Issue Detection**: View detailed detection results with timing and parameters
- **Export Reports**: Download text summaries of detected issues


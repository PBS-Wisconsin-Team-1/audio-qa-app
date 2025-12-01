"""
Flask API server for the Audio QA frontend.
Serves detection reports and handles file uploads.
"""
import os
import json
import redis
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
DETECTION_RESULTS_DIR = os.path.join('..', '..', 'detection_results')
AUDIO_FILES_DIR = os.path.join('..', '..', 'audio_files')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

def get_processed_files():
    """Scan detection_results directory and return list of processed files."""
    files = []
    
    if not os.path.exists(DETECTION_RESULTS_DIR):
        return files
    
    for item in os.listdir(DETECTION_RESULTS_DIR):
        item_path = os.path.join(DETECTION_RESULTS_DIR, item)
        if os.path.isdir(item_path):
            # Look for report JSON files
            for file in os.listdir(item_path):
                if file.endswith('_report.json'):
                    report_path = os.path.join(item_path, file)
                    try:
                        with open(report_path, 'r') as f:
                            report_data = json.load(f)
                        
                        # Handle new format (object with title, file, overall_results, in_file_detections)
                        # or old format (array of detections)
                        if isinstance(report_data, dict):
                            # New format
                            base_name = report_data.get('file', file.replace('_report.json', ''))
                            issue_count = len(report_data.get('in_file_detections', []))
                        else:
                            # Old format (backward compatibility)
                            base_name = file.replace('_report.json', '')
                            issue_count = len(report_data) if isinstance(report_data, list) else 0
                        
                        # Extract timestamp from directory name
                        # Format: {base_name}_{timestamp} or just timestamp
                        # Try to find timestamp pattern in directory name
                        timestamp_str = None
                        dir_parts = item.split('_')
                        
                        # Look for YYYY-MM-DD_HH-MM-SS pattern (last 2 parts if they match)
                        if len(dir_parts) >= 2:
                            potential_timestamp = '_'.join(dir_parts[-2:])
                            try:
                                datetime.strptime(potential_timestamp, '%Y-%m-%d_%H-%M-%S')
                                timestamp_str = potential_timestamp
                            except ValueError:
                                pass
                        
                        # If no timestamp found, try the whole directory name
                        if not timestamp_str:
                            try:
                                datetime.strptime(item, '%Y-%m-%d_%H-%M-%S')
                                timestamp_str = item
                            except ValueError:
                                pass
                        
                        if timestamp_str:
                            try:
                                processed_date = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                                formatted_date = processed_date.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                formatted_date = item
                        else:
                            # Use directory modification time as fallback
                            try:
                                mtime = os.path.getmtime(item_path)
                                formatted_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                formatted_date = item
                        
                        files.append({
                            'id': item,  # Use directory name as ID
                            'name': base_name,
                            'issueCount': issue_count,
                            'processedDate': formatted_date,
                            'reportPath': report_path
                        })
                    except Exception as e:
                        print(f"Error reading report {report_path}: {e}")
                        continue
    
    # Sort by processed date (newest first)
    files.sort(key=lambda x: x['processedDate'], reverse=True)
    return files

@app.route('/api/files', methods=['GET'])
def list_files():
    """Get list of all processed files."""
    try:
        files = get_processed_files()
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/report', methods=['GET'])
def get_report(file_id):
    """Get detection report for a specific file."""
    try:
        # Find the report file
        file_dir = os.path.join(DETECTION_RESULTS_DIR, file_id)
        if not os.path.exists(file_dir):
            return jsonify({'error': 'File not found'}), 404
        
        # Look for report JSON
        report_file = None
        for file in os.listdir(file_dir):
            if file.endswith('_report.json'):
                report_file = os.path.join(file_dir, file)
                break
        
        if not report_file:
            return jsonify({'error': 'Report not found'}), 404
        
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        return jsonify(report_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Get current queue status from Redis."""
    try:
        redis_conn = redis.from_url(REDIS_URL)
        
        # Get all job statuses
        job_statuses = redis_conn.hgetall('job_status')
        
        total = len(job_statuses)
        completed = sum(1 for status in job_statuses.values() if status.decode('utf-8') == 'completed')
        queued = sum(1 for status in job_statuses.values() if status.decode('utf-8') == 'queued')
        in_progress = total - completed - queued
        
        return jsonify({
            'total': total,
            'completed': completed,
            'queued': queued,
            'inProgress': in_progress
        })
    except redis.ConnectionError:
        # Redis not available, return empty status
        return jsonify({
            'total': 0,
            'completed': 0,
            'queued': 0,
            'inProgress': 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file to audio_files directory
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
        file_path = os.path.join(AUDIO_FILES_DIR, file.filename)
        file.save(file_path)
        
        # TODO: Queue the file for processing
        # For now, just return success
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': file.filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information."""
    return jsonify({
        'message': 'Audio QA API Server',
        'status': 'ok',
        'frontend': 'http://localhost:3000',
        'endpoints': {
            '/api': 'GET - List all API endpoints',
            '/api/files': 'GET - List all processed files',
            '/api/files/<file_id>/report': 'GET - Get detection report for a file',
            '/api/queue/status': 'GET - Get queue status',
            '/api/upload': 'POST - Upload audio file',
            '/api/health': 'GET - Health check'
        }
    })

@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Audio QA API Server',
        'endpoints': {
            'files': '/api/files',
            'file_report': '/api/files/<file_id>/report',
            'queue_status': '/api/queue/status',
            'upload': '/api/upload',
            'health': '/api/health'
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(DETECTION_RESULTS_DIR, exist_ok=True)
    os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
    
    # Use port 5001 by default (5000 is often used by AirPlay on macOS)
    port = int(os.getenv('API_PORT', 5001))
    
    print(f"Starting API server...")
    print(f"Detection results directory: {DETECTION_RESULTS_DIR}")
    print(f"Audio files directory: {AUDIO_FILES_DIR}")
    print(f"Redis URL: {REDIS_URL}")
    print(f"API server running on http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=True)


"""
Flask API server for the Audio QA frontend.
Serves detection reports and handles file uploads.
"""
import os
import sys
import json
import redis
import shutil
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
from pathlib import Path

# Add src directory to path so imports work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
DETECTION_RESULTS_DIR = os.path.join(PROJECT_ROOT, 'detection_results')
DEFAULT_AUDIO_FILES_DIR = os.path.join(PROJECT_ROOT, 'audio_files')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Config file to store audio directory preference
CONFIG_FILE = os.path.join(PROJECT_ROOT, '.audio_qa_config.json')

def get_audio_files_dir():
    """Get the configured audio files directory, or default if not set."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                audio_dir = config.get('audio_files_dir')
                if audio_dir and os.path.exists(audio_dir):
                    return audio_dir
        except Exception as e:
            print(f"Error reading config file: {e}")
    return DEFAULT_AUDIO_FILES_DIR

def set_audio_files_dir(path):
    """Set the audio files directory in config file."""
    try:
        config = {'audio_files_dir': path}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing config file: {e}")
        return False

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

@app.route('/api/files/<file_id>/clips/<clip_filename>', methods=['GET'])
def get_clip(file_id, clip_filename):
    """Serve audio clip file for a specific detection."""
    try:
        # Find the clips directory
        file_dir = os.path.join(DETECTION_RESULTS_DIR, file_id)
        clips_dir = os.path.join(file_dir, 'clips')
        
        if not os.path.exists(clips_dir):
            return jsonify({'error': 'Clips directory not found'}), 404
        
        clip_path = os.path.join(clips_dir, clip_filename)
        
        # Security check: ensure the clip is within the clips directory
        if not os.path.abspath(clip_path).startswith(os.path.abspath(clips_dir)):
            return jsonify({'error': 'Invalid clip path'}), 400
        
        if not os.path.exists(clip_path):
            return jsonify({'error': 'Clip not found'}), 404
        
        # Serve the audio file
        return send_from_directory(clips_dir, clip_filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/delete', methods=['POST'])
def delete_files():
    """Delete one or more processed files."""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids or not isinstance(file_ids, list):
            return jsonify({'error': 'file_ids must be a non-empty array'}), 400
        
        deleted = []
        errors = []
        
        for file_id in file_ids:
            try:
                file_dir = os.path.join(DETECTION_RESULTS_DIR, file_id)
                
                # Security check: ensure the directory is within DETECTION_RESULTS_DIR
                if not os.path.abspath(file_dir).startswith(os.path.abspath(DETECTION_RESULTS_DIR)):
                    errors.append({'file_id': file_id, 'error': 'Invalid file path'})
                    continue
                
                if os.path.exists(file_dir):
                    shutil.rmtree(file_dir)
                    deleted.append(file_id)
                else:
                    errors.append({'file_id': file_id, 'error': 'File not found'})
            except Exception as e:
                errors.append({'file_id': file_id, 'error': str(e)})
        
        return jsonify({
            'deleted': deleted,
            'errors': errors,
            'message': f'Deleted {len(deleted)} file(s)'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/export', methods=['POST'])
def export_files():
    """Get reports for multiple files for bulk export."""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids or not isinstance(file_ids, list):
            return jsonify({'error': 'file_ids must be a non-empty array'}), 400
        
        reports = []
        errors = []
        
        for file_id in file_ids:
            try:
                file_dir = os.path.join(DETECTION_RESULTS_DIR, file_id)
                if not os.path.exists(file_dir):
                    errors.append({'file_id': file_id, 'error': 'File not found'})
                    continue
                
                # Look for report JSON
                report_file = None
                for file in os.listdir(file_dir):
                    if file.endswith('_report.json'):
                        report_file = os.path.join(file_dir, file)
                        break
                
                if not report_file:
                    errors.append({'file_id': file_id, 'error': 'Report not found'})
                    continue
                
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                    reports.append({
                        'file_id': file_id,
                        'report': report_data
                    })
            except Exception as e:
                errors.append({'file_id': file_id, 'error': str(e)})
        
        return jsonify({
            'reports': reports,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detection-types', methods=['GET'])
def get_detection_types():
    """Get available detection types and their default parameters."""
    try:
        from .analysis_types import ANALYSIS_TYPES
        
        detection_types = {}
        for det_type, config in ANALYSIS_TYPES.items():
            detection_types[det_type] = {
                'type': config.get('type', 'in-file'),
                'params': config.get('params', {}),
                'description': config.get('description', '')
            }
        
        return jsonify({
            'detection_types': detection_types
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/job', methods=['POST'])
def queue_job():
    """Queue audio files for processing with custom detection types and parameters."""
    try:
        data = request.get_json()
        file_names = data.get('file_names', [])
        detection_params = data.get('detection_params', {})
        clip_pad = data.get('clip_pad', 0.1)
        
        if not file_names or not isinstance(file_names, list):
            return jsonify({'error': 'file_names must be a non-empty array'}), 400
        
        if not detection_params or not isinstance(detection_params, dict):
            return jsonify({'error': 'detection_params must be a dictionary'}), 400
        
        # Import here to avoid circular imports
        from audio_processing.audio_import import AudioLoader
        from .worker import AudioDetectionJob
        from .analysis_types import ANALYSIS_TYPES
        from rq import Queue
        
        # Validate detection types
        for det_type in detection_params.keys():
            if det_type not in ANALYSIS_TYPES:
                return jsonify({'error': f'Invalid detection type: {det_type}'}), 400
        
        AUDIO_FILES_DIR = get_audio_files_dir()
        loader = AudioLoader(directory=AUDIO_FILES_DIR)
        
        # Queue the files
        try:
            redis_conn = redis.from_url(REDIS_URL)
            redis_conn.ping()
            job_queue = Queue(connection=redis_conn)
            
            queued = []
            errors = []
            
            for file_name in file_names:
                try:
                    # Validate file exists
                    file_path = os.path.join(AUDIO_FILES_DIR, file_name)
                    if not os.path.exists(file_path):
                        errors.append({'file': file_name, 'error': 'File not found'})
                        continue
                    
                    # Create job and queue it
                    job = AudioDetectionJob(loader, file_name, REDIS_URL, clip_pad=clip_pad)
                    job_queue.enqueue(job.load_and_queue, detection_params)
                    queued.append(file_name)
                except Exception as e:
                    errors.append({'file': file_name, 'error': str(e)})
            
            return jsonify({
                'message': f'Queued {len(queued)} file(s) for processing',
                'queued': queued,
                'errors': errors
            })
        except redis.ConnectionError:
            return jsonify({'error': 'Redis not available. Please ensure Redis is running.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Get current queue status from Redis.
    
    Optional query parameter:
    - since: Unix timestamp - only count jobs created after this time
    """
    try:
        redis_conn = redis.from_url(REDIS_URL)
        
        # Get optional 'since' timestamp parameter
        since_timestamp = request.args.get('since', type=int)
        
        # Get all job statuses
        job_statuses = redis_conn.hgetall('job_status')
        
        # Filter by timestamp if provided and group by file
        # Job keys are in format: {audio_base}_{type}_{timestamp}
        # We want to group by {audio_base}_{timestamp} to count files, not individual detection jobs
        
        file_groups = {}  # Key: {audio_base}_{timestamp}, Value: list of (job_key, status)
        
        for job_key, status in job_statuses.items():
            job_key_str = job_key.decode('utf-8') if isinstance(job_key, bytes) else job_key
            status_str = status.decode('utf-8') if isinstance(status, bytes) else status
            
            # Extract timestamp from the key
            try:
                # Split by underscore and get the last part (timestamp)
                parts = job_key_str.rsplit('_', 1)
                if len(parts) == 2:
                    job_timestamp = int(parts[1])
                    
                    # Filter by timestamp if provided
                    if since_timestamp and job_timestamp < since_timestamp:
                        continue
                    
                    # Extract file identifier: everything before the last underscore (which is timestamp)
                    # But we need to remove the detection type too
                    # Format is: {audio_base}_{type}_{timestamp}
                    # We want: {audio_base}_{timestamp}
                    file_key_parts = parts[0].rsplit('_', 1)  # Split to get {audio_base} and {type}
                    if len(file_key_parts) == 2:
                        audio_base = file_key_parts[0]
                        file_key = f"{audio_base}_{parts[1]}"  # {audio_base}_{timestamp}
                    else:
                        # Fallback: use the whole thing before timestamp
                        file_key = parts[0]
                    
                    if file_key not in file_groups:
                        file_groups[file_key] = []
                    file_groups[file_key].append((job_key_str, status_str))
                else:
                    # If we can't parse, treat each job as a separate file (backward compatibility)
                    file_key = job_key_str
                    if file_key not in file_groups:
                        file_groups[file_key] = []
                    file_groups[file_key].append((job_key_str, status_str))
            except (ValueError, IndexError):
                # If we can't parse, treat each job as a separate file (backward compatibility)
                file_key = job_key_str
                if file_key not in file_groups:
                    file_groups[file_key] = []
                file_groups[file_key].append((job_key_str, status_str))
        
        # Count files by their status
        # A file is "completed" only when ALL its detection jobs are completed
        # A file is "queued" if ANY of its detection jobs are queued (and not all completed)
        # A file is "in progress" if it has some jobs in progress but not all completed
        
        completed_files = 0
        queued_files = 0
        in_progress_files = 0
        
        for file_key, jobs in file_groups.items():
            statuses = [status for _, status in jobs]
            
            # Check if all jobs are completed
            all_completed = all(s == 'completed' for s in statuses)
            if all_completed:
                completed_files += 1
            else:
                # Check if any job is queued
                has_queued = any(s == 'queued' for s in statuses)
                if has_queued:
                    queued_files += 1
                else:
                    # Has some jobs in progress or other status
                    in_progress_files += 1
        
        total = len(file_groups)
        
        return jsonify({
            'total': total,
            'completed': completed_files,
            'queued': queued_files,
            'inProgress': in_progress_files
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
    """Handle file upload and automatically queue for processing."""
    try:
        print(f"Upload request received. Files: {list(request.files.keys())}")
        if 'file' not in request.files:
            print("Error: No 'file' key in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("Error: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Processing file: {file.filename}")
        
        # Save file to audio_files directory
        AUDIO_FILES_DIR = get_audio_files_dir()
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
        file_path = os.path.join(AUDIO_FILES_DIR, file.filename)
        file.save(file_path)
        
        # Get detection types from query parameter (default to all)
        detection_types_param = request.args.get('detection_types', 'all')
        
        # Import here to avoid circular imports
        from audio_processing.audio_import import AudioLoader
        from .worker import AudioDetectionJob
        from .analysis_types import ANALYSIS_TYPES
        from rq import Queue
        
        # Queue the file for processing
        try:
            redis_conn = redis.from_url(REDIS_URL)
            redis_conn.ping()
            job_queue = Queue(connection=redis_conn)
            
            loader = AudioLoader(directory=AUDIO_FILES_DIR)
            audio_file_path = file.filename  # Relative path from configured audio directory
            
            # Determine which detection types to run
            if detection_types_param.lower() == 'all':
                detection_params = {det_type: {} for det_type in ANALYSIS_TYPES.keys()}
            else:
                # Parse comma-separated list of detection types
                requested_types = [t.strip() for t in detection_types_param.split(',')]
                detection_params = {}
                for det_type in requested_types:
                    if det_type in ANALYSIS_TYPES:
                        detection_params[det_type] = {}
            
            if not detection_params:
                return jsonify({
                    'message': 'File uploaded successfully but no valid detection types specified',
                    'filename': file.filename
                }), 200
            
            # Create job and queue it
            job = AudioDetectionJob(loader, audio_file_path, REDIS_URL)
            job_queue.enqueue(job.load_and_queue, detection_params)
            
            return jsonify({
                'message': 'File uploaded and queued for processing successfully',
                'filename': file.filename,
                'detection_types': list(detection_params.keys())
            })
        except redis.ConnectionError:
            return jsonify({
                'message': 'File uploaded successfully, but could not queue for processing (Redis not available)',
                'filename': file.filename,
                'warning': 'Please ensure Redis is running and queue the file manually'
            }), 200
        except Exception as queue_error:
            return jsonify({
                'message': 'File uploaded successfully, but failed to queue for processing',
                'filename': file.filename,
                'error': str(queue_error)
            }), 200
        
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

@app.route('/api/config/audio-dir', methods=['GET'])
def get_audio_dir():
    """Get the current audio files directory."""
    try:
        audio_dir = get_audio_files_dir()
        return jsonify({
            'audio_dir': audio_dir,
            'exists': os.path.exists(audio_dir),
            'is_default': audio_dir == DEFAULT_AUDIO_FILES_DIR
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/audio-dir', methods=['POST'])
def set_audio_dir():
    """Set the audio files directory."""
    try:
        data = request.get_json()
        new_dir = data.get('audio_dir', '').strip()
        
        if not new_dir:
            return jsonify({'error': 'No directory path provided'}), 400
        
        # Validate path exists
        if not os.path.exists(new_dir):
            return jsonify({'error': f'Directory does not exist: {new_dir}'}), 400
        
        if not os.path.isdir(new_dir):
            return jsonify({'error': f'Path is not a directory: {new_dir}'}), 400
        
        # Set the directory
        if set_audio_files_dir(new_dir):
            return jsonify({
                'message': 'Audio directory updated successfully',
                'audio_dir': new_dir
            })
        else:
            return jsonify({'error': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/list', methods=['GET'])
def list_audio_files():
    """List audio files in the configured audio directory."""
    try:
        audio_dir = get_audio_files_dir()
        if not os.path.exists(audio_dir):
            return jsonify({'error': 'Audio directory does not exist'}), 404
        
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma']
        files = []
        
        for filename in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename)
                if ext.lower() in audio_extensions:
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        files.sort(key=lambda x: x['name'])
        return jsonify({
            'audio_dir': audio_dir,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

def main():
    """Main entry point for the API server."""
    # Ensure directories exist
    os.makedirs(DETECTION_RESULTS_DIR, exist_ok=True)
    audio_dir = get_audio_files_dir()
    os.makedirs(audio_dir, exist_ok=True)
    
    # Use port 5001 by default (5000 is often used by AirPlay on macOS)
    port = int(os.getenv('API_PORT', 5001))
    
    print(f"Starting API server...")
    print(f"Detection results directory: {DETECTION_RESULTS_DIR}")
    print(f"Audio files directory: {audio_dir}")
    print(f"Redis URL: {REDIS_URL}")
    print(f"API server running on http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()

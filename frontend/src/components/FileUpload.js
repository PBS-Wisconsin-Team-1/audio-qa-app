import React, { useState } from 'react';
import { uploadAudioFile } from '../services/api';
import './FileUpload.css';

const FileUpload = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const audioFiles = files.filter(file => 
      file.type.startsWith('audio/') || 
      /\.(wav|mp3|flac|ogg|m4a)$/i.test(file.name)
    );
    
    if (audioFiles.length > 0) {
      // Upload files sequentially
      for (const file of audioFiles) {
        await handleFileUpload(file);
      }
    } else {
      setError('Please drop audio files (WAV, MP3, FLAC, etc.)');
    }
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      // Upload files sequentially
      for (const file of files) {
        await handleFileUpload(file);
      }
      // Reset input to allow selecting the same file again
      e.target.value = '';
    }
  };

  const handleFileUpload = async (file) => {
    setError(null);
    setSuccess(null);
    setUploading(true);
    
    try {
      const result = await uploadAudioFile(file);
      const message = result.detection_types 
        ? `✓ ${file.name} uploaded and queued for processing (${result.detection_types.length} detection types)`
        : result.message || `✓ ${file.name} uploaded successfully`;
      setSuccess(message);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      console.error('Upload error details:', err);
      const errorMessage = err.message || 'Failed to upload file. Please check the console for details.';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <h3>Upload Audio Files</h3>
      <div
        className={`file-upload-area ${isDragging ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {uploading ? (
          <div className="file-upload-content">
            <div className="file-upload-spinner"></div>
            <p>Uploading...</p>
          </div>
        ) : (
          <>
            <div className="file-upload-icon">📤</div>
            <p className="file-upload-text">
              Drag and drop audio files here, or click to browse
            </p>
            <p className="file-upload-hint">
              You can select multiple files from anywhere on your computer
            </p>
            <input
              type="file"
              accept="audio/*,.wav,.mp3,.flac,.ogg,.m4a"
              onChange={handleFileSelect}
              className="file-upload-input"
              disabled={uploading}
              multiple
            />
          </>
        )}
      </div>
      {error && (
        <div className="file-upload-error">
          {error}
        </div>
      )}
      {success && (
        <div className="file-upload-success">
          {success}
        </div>
      )}
    </div>
  );
};

export default FileUpload;


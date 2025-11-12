import React, { useState } from 'react';
import { uploadAudioFile } from '../services/api';
import './FileUpload.css';

const FileUpload = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

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
    const audioFile = files.find(file => 
      file.type.startsWith('audio/') || 
      /\.(wav|mp3|flac|ogg|m4a)$/i.test(file.name)
    );
    
    if (audioFile) {
      await handleFileUpload(audioFile);
    } else {
      setError('Please drop an audio file (WAV, MP3, FLAC, etc.)');
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (file) {
      await handleFileUpload(file);
    }
  };

  const handleFileUpload = async (file) => {
    setError(null);
    setUploading(true);
    
    try {
      const result = await uploadAudioFile(file);
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <h3>Upload Audio File</h3>
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
              Drag and drop an audio file here, or click to browse
            </p>
            <input
              type="file"
              accept="audio/*,.wav,.mp3,.flac,.ogg,.m4a"
              onChange={handleFileSelect}
              className="file-upload-input"
              disabled={uploading}
            />
          </>
        )}
      </div>
      {error && (
        <div className="file-upload-error">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUpload;


const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

/**
 * Fetch all processed files (detection results)
 */
export const getProcessedFiles = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/files`);
    if (!response.ok) {
      throw new Error('Failed to fetch processed files');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching processed files:', error);
    throw error;
  }
};

/**
 * Fetch detection report for a specific file
 */
export const getDetectionReport = async (fileId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/report`);
    if (!response.ok) {
      throw new Error('Failed to fetch detection report');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching detection report:', error);
    throw error;
  }
};

/**
 * Get queue status
 */
export const getQueueStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/queue/status`);
    if (!response.ok) {
      throw new Error('Failed to fetch queue status');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching queue status:', error);
    throw error;
  }
};

/**
 * Upload audio file
 */
export const uploadAudioFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to upload file');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};


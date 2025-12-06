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
 * Open AUQA CLI in a new terminal window
 */
export const openCli = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/open-cli`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error('Failed to open CLI');
    }
    return await response.json();
  } catch (error) {
    console.error('Error opening CLI:', error);
    throw error;
  }
};

/**
 * Get queue status
 * @param {number} sinceTimestamp - Optional Unix timestamp (seconds) to only count jobs created after this time
 */
export const getQueueStatus = async (sinceTimestamp = null) => {
  try {
    let url = `${API_BASE_URL}/queue/status`;
    if (sinceTimestamp) {
      url += `?since=${sinceTimestamp}`;
    }
    const response = await fetch(url);
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
    
    const data = await response.json();
    
    if (!response.ok) {
      // Use server error message if available
      const errorMessage = data.error || data.message || 'Failed to upload file';
      throw new Error(errorMessage);
    }
    
    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

/**
 * Get current audio directory configuration
 */
export const getAudioDir = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/config/audio-dir`);
    if (!response.ok) {
      throw new Error('Failed to fetch audio directory');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching audio directory:', error);
    throw error;
  }
};

/**
 * Set audio directory configuration
 */
export const setAudioDir = async (audioDir) => {
  try {
    const response = await fetch(`${API_BASE_URL}/config/audio-dir`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ audio_dir: audioDir }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      const errorMessage = data.error || 'Failed to set audio directory';
      throw new Error(errorMessage);
    }
    
    return data;
  } catch (error) {
    console.error('Error setting audio directory:', error);
    throw error;
  }
};

/**
 * List audio files in the configured directory
 */
export const listAudioFiles = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/files/list`);
    if (!response.ok) {
      throw new Error('Failed to list audio files');
    }
    return await response.json();
  } catch (error) {
    console.error('Error listing audio files:', error);
    throw error;
  }
};

/**
 * Delete one or more processed files
 */
export const deleteFiles = async (fileIds) => {
  try {
    const response = await fetch(`${API_BASE_URL}/files/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_ids: fileIds }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      const errorMessage = data.error || 'Failed to delete files';
      throw new Error(errorMessage);
    }
    
    return data;
  } catch (error) {
    console.error('Error deleting files:', error);
    throw error;
  }
};

/**
 * Get reports for multiple files (for bulk export)
 */
export const getBulkReports = async (fileIds) => {
  try {
    const response = await fetch(`${API_BASE_URL}/files/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_ids: fileIds }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      const errorMessage = data.error || 'Failed to fetch reports';
      throw new Error(errorMessage);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching bulk reports:', error);
    throw error;
  }
};


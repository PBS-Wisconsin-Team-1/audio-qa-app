/**
 * Generate a text summary of all detected issues
 */
export const generateTextSummary = (fileName, reportTitle, overallResults, detections, metadata = {}) => {
  let summary = reportTitle ? `${reportTitle}\n` : `AuQA Report\n`;
  summary += `================================\n\n`;
  summary += `File: ${fileName}\n`;
  summary += `Generated: ${new Date().toLocaleString()}\n`;
  
  // Add metadata if available
  if (metadata.duration) {
    summary += `Duration: ${metadata.duration}\n`;
  }
  if (metadata.samplerate) {
    const samplerate = typeof metadata.samplerate === 'number' 
      ? metadata.samplerate.toFixed(0) 
      : metadata.samplerate;
    summary += `Sample Rate: ${samplerate} Hz\n`;
  }
  if (metadata.channels) {
    const channels = typeof metadata.channels === 'number' 
      ? (metadata.channels === 1 ? 'mono' : metadata.channels === 2 ? 'stereo' : `${metadata.channels} channels`)
      : metadata.channels;
    summary += `Channels: ${channels}\n`;
  }
  
  summary += `\n`;
  
  const hasOverallResults = overallResults && overallResults.length > 0;
  const hasDetections = detections && detections.length > 0;
  
  if (!hasOverallResults && !hasDetections) {
    summary += `No issues detected. Audio quality is good.\n`;
    return summary;
  }
  
  // Overall Results Section
  if (hasOverallResults) {
    summary += `Overall Results:\n`;
    summary += `----------------\n`;
    overallResults.forEach((result, index) => {
      summary += `${index + 1}. ${result.type}: `;
      summary += typeof result.result === 'number' 
        ? result.result.toFixed(2) 
        : result.result;
      summary += `\n`;
      if (result.params && Object.keys(result.params).length > 0) {
        summary += `   Parameters: ${JSON.stringify(result.params)}\n`;
      }
      summary += `\n`;
    });
  }
  
  // Detections Section
  if (hasDetections) {
    summary += `Total Issues Detected: ${detections.length}\n\n`;
    
    // Group by type
    const issuesByType = detections.reduce((acc, detection) => {
      const type = detection.type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(detection);
      return acc;
    }, {});
    
    // Summary by type
    summary += `Summary by Issue Type:\n`;
    summary += `----------------------\n`;
    Object.entries(issuesByType).forEach(([type, issues]) => {
      summary += `  ${type}: ${issues.length} issue(s)\n`;
    });
    summary += `\n`;
    
    // Detailed list - grouped by type with parameters shown once
    summary += `Detailed Issue List:\n`;
    summary += `--------------------\n\n`;
    
    let globalIndex = 1;
    Object.entries(issuesByType).forEach(([type, typeDetections]) => {
      const firstDetection = typeDetections[0];
      const params = firstDetection.params || {};
      
      // Get common details text (same for all instances of this type)
      let commonDetails = null;
      if (firstDetection.details) {
        let detailsText = firstDetection.details;
        // Remove ClipDaT algorithm messages for Clipping
        if (type === 'Clipping') {
          detailsText = detailsText.replace(/Detected using clipdetect library's ClipDaT algorithm implementation/gi, '');
          detailsText = detailsText.replace(/Clipping detected by ClipDaT algorithm/gi, '');
          detailsText = detailsText.replace(/Clipping detected/gi, '').trim();
          if (!detailsText || detailsText.length === 0) {
            detailsText = null;
          }
        }
        // Only show details if they're the same across all instances
        const allSameDetails = typeDetections.every(d => {
          let dDetails = d.details || '';
          if (type === 'Clipping') {
            dDetails = dDetails.replace(/Detected using clipdetect library's ClipDaT algorithm implementation/gi, '');
            dDetails = dDetails.replace(/Clipping detected by ClipDaT algorithm/gi, '');
            dDetails = dDetails.replace(/Clipping detected/gi, '').trim();
          }
          return dDetails === detailsText;
        });
        if (allSameDetails && detailsText) {
          commonDetails = detailsText;
        }
      }
      
      // Format parameter helper function
      const formatParameter = (key, value) => {
        let displayValue = value;
        let unit = '';
        
        if (typeof value === 'boolean') {
          displayValue = value ? 'enabled' : 'disabled';
        } else if (typeof value === 'number') {
          if (key === 'min_len' || key.includes('ms') || key.includes('duration')) {
            unit = ' ms';
          } else if (key === 'threshold') {
            displayValue = Number.isInteger(value) ? value : value.toFixed(3);
          } else if (key.includes('window') || key.includes('time')) {
            unit = ' s';
            displayValue = Number.isInteger(value) ? value : value.toFixed(2);
          } else {
            displayValue = Number.isInteger(value) ? value : value.toFixed(3);
          }
        }
        
        const formattedKey = key
          .replace(/_/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase());
        
        return { formattedKey, displayValue, unit };
      };
      
      summary += `${type} (${typeDetections.length} detection${typeDetections.length !== 1 ? 's' : ''})\n`;
      summary += `${'='.repeat(type.length + 20)}\n`;
      
      // Show common description once
      if (commonDetails) {
        summary += `Description: ${commonDetails}\n`;
      }
      
      // Show parameters once at the top (if any)
      if (Object.keys(params).length > 0) {
        summary += `Detection Parameters:\n`;
        Object.entries(params).forEach(([key, value]) => {
          const { formattedKey, displayValue, unit } = formatParameter(key, value);
          summary += `  ${formattedKey}: ${displayValue}${unit}\n`;
        });
      }
      
      // List all timestamps
      summary += `Detection Instances:\n`;
      typeDetections.forEach((detection) => {
        summary += `  • ${detection.start_mmss}`;
        if (detection.end !== null && detection.end_mmss !== 'N/A') {
          summary += ` - ${detection.end_mmss}`;
        }
        summary += `\n`;
      });
      
      summary += `\n`;
      globalIndex += typeDetections.length;
    });
  }
  
  return summary;
};

/**
 * Download text file
 */
export const downloadTextFile = (content, filename) => {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};


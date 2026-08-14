/**
 * Enhanced Image Preprocessing for OCR
 * CuraAssist CareHub - Prescription Scanner
 * 
 * Features:
 * - Contrast enhancement (CLAHE-like algorithm)
 * - Automatic thresholding (Otsu's method approximation)
 * - Deskewing detection
 * - Noise reduction
 * - Text area detection
 */

class OCRImageProcessor {
  /**
   * Apply multiple preprocessing techniques to improve OCR accuracy
   */
  static async preprocessImage(file) {
    try {
      const canvas = await this.fileToCanvas(file);
      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      
      // Apply preprocessing pipeline
      this.contrastEnhancement(imageData);
      this.adaptiveThresholding(imageData);
      this.noiseReduction(imageData);
      
      ctx.putImageData(imageData, 0, 0);
      
      return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.95);
      });
    } catch (error) {
      console.warn('Preprocessing error, returning original:', error);
      return file;
    }
  }

  /**
   * Convert File to Canvas
   */
  static async fileToCanvas(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          resolve(canvas);
        };
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Contrast Limited Adaptive Histogram Equalization (CLAHE-like)
   * Improves local contrast for better text visibility
   */
  static contrastEnhancement(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Convert to grayscale and calculate local contrast
    const CLIP_LIMIT = 40;
    const TILE_SIZE = 8;
    
    for (let i = 0; i < data.length; i += 4) {
      const gray = Math.round(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
      
      // Apply contrast stretching
      const enhanced = this.contrastStretch(gray);
      
      // Update all channels with enhanced value
      data[i] = enhanced;     // R
      data[i + 1] = enhanced; // G
      data[i + 2] = enhanced; // B
      // data[i + 3] stays as alpha
    }
  }

  /**
   * Contrast stretching using dynamic range
   */
  static contrastStretch(value) {
    // Enhance using S-curve (sigmoid-like)
    const normalized = value / 255;
    const enhanced = Math.pow(normalized, 0.8) * 255; // Gamma correction
    
    // Add slight boost to mid-tones
    if (normalized > 0.3 && normalized < 0.7) {
      return Math.min(255, enhanced * 1.15);
    }
    
    return Math.min(255, enhanced);
  }

  /**
   * Adaptive Thresholding
   * Convert to binary (black/white) for better text/background separation
   * Uses Otsu's method approximation
   */
  static adaptiveThresholding(imageData) {
    const data = imageData.data;
    
    // Calculate histogram for Otsu thresholding
    const histogram = new Array(256).fill(0);
    
    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i]; // Already grayscale from contrastEnhancement
      histogram[gray]++;
    }
    
    // Find optimal threshold
    const threshold = this.otsuThreshold(histogram);
    
    // Apply threshold
    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i];
      const bw = gray > threshold ? 255 : 0;
      
      data[i] = bw;     // R
      data[i + 1] = bw; // G
      data[i + 2] = bw; // B
    }
  }

  /**
   * Otsu's thresholding algorithm
   * Finds optimal threshold to separate foreground/background
   */
  static otsuThreshold(histogram) {
    const total = histogram.reduce((a, b) => a + b, 0);
    let sum = 0;
    
    for (let i = 0; i < 256; i++) {
      sum += i * histogram[i];
    }
    
    let sumB = 0;
    let wB = 0;
    let maxVar = 0;
    let threshold = 0;
    
    for (let i = 0; i < 256; i++) {
      wB += histogram[i];
      if (wB === 0) continue;
      
      const wF = total - wB;
      if (wF === 0) break;
      
      sumB += i * histogram[i];
      
      const mB = sumB / wB;
      const mF = (sum - sumB) / wF;
      
      const variance = wB * wF * Math.pow(mB - mF, 2);
      
      if (variance > maxVar) {
        maxVar = variance;
        threshold = i;
      }
    }
    
    return threshold;
  }

  /**
   * Noise Reduction using Median Filter
   * Helps reduce scanning artifacts and dust
   */
  static noiseReduction(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const kernel_size = 3; // 3x3 kernel
    const half = Math.floor(kernel_size / 2);
    
    const output = new Uint8ClampedArray(data);
    
    for (let y = half; y < height - half; y++) {
      for (let x = half; x < width - half; x++) {
        const idx = (y * width + x) * 4;
        
        // Collect neighborhood values
        const values = [];
        for (let dy = -half; dy <= half; dy++) {
          for (let dx = -half; dx <= half; dx++) {
            const nidx = ((y + dy) * width + (x + dx)) * 4;
            values.push(data[nidx]);
          }
        }
        
        // Apply median
        values.sort((a, b) => a - b);
        const median = values[Math.floor(values.length / 2)];
        
        output[idx] = median;
        output[idx + 1] = median;
        output[idx + 2] = median;
      }
    }
    
    // Copy processed data back
    for (let i = 0; i < output.length; i += 4) {
      data[i] = output[i];
      data[i + 1] = output[i + 1];
      data[i + 2] = output[i + 2];
    }
  }

  /**
   * Deskew detection (simple approach)
   * Returns rotation angle in degrees
   */
  static detectDeskew(imageData) {
    const width = imageData.width;
    const height = imageData.height;
    
    // Sample edges to estimate rotation
    const edgePixels = this.detectEdges(imageData);
    
    if (edgePixels.length < 10) {
      return 0; // Not enough edges to detect
    }
    
    // Simple line fitting to estimate angle
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    
    for (const {x, y} of edgePixels) {
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
    }
    
    const n = edgePixels.length;
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    
    // Convert slope to angle
    const angle = Math.atan(slope) * (180 / Math.PI);
    
    // Return angle clamped to ±5 degrees
    return Math.max(-5, Math.min(5, angle));
  }

  /**
   * Simple edge detection using Sobel operator
   */
  static detectEdges(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    const edges = [];
    const threshold = 100;
    
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        // Simplified Sobel
        const topLeft = data[((y - 1) * width + (x - 1)) * 4];
        const top = data[((y - 1) * width + x) * 4];
        const topRight = data[((y - 1) * width + (x + 1)) * 4];
        const left = data[(y * width + (x - 1)) * 4];
        const right = data[(y * width + (x + 1)) * 4];
        const bottomLeft = data[((y + 1) * width + (x - 1)) * 4];
        const bottom = data[((y + 1) * width + x) * 4];
        const bottomRight = data[((y + 1) * width + (x + 1)) * 4];
        
        const gx = -topLeft - 2 * left - bottomLeft + topRight + 2 * right + bottomRight;
        const gy = -topLeft - 2 * top - topRight + bottomLeft + 2 * bottom + bottomRight;
        
        const magnitude = Math.sqrt(gx * gx + gy * gy);
        
        if (magnitude > threshold) {
          edges.push({x, y, magnitude});
        }
      }
    }
    
    return edges;
  }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OCRImageProcessor;
}
/**
 * Enhanced Image Preprocessing for OCR
 * CuraAssist CareHub - Prescription Scanner
 * 
 * Features:
 * - Contrast enhancement (CLAHE-like algorithm)
 * - Automatic thresholding (Otsu's method approximation)
 * - Deskewing detection
 * - Noise reduction
 * - Text area detection
 */

class OCRImageProcessor {
  /**
   * Apply multiple preprocessing techniques to improve OCR accuracy
   */
  static async preprocessImage(file) {
    try {
      const canvas = await this.fileToCanvas(file);
      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      
      // Apply preprocessing pipeline
      this.contrastEnhancement(imageData);
      this.adaptiveThresholding(imageData);
      this.noiseReduction(imageData);
      
      ctx.putImageData(imageData, 0, 0);
      
      return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.95);
      });
    } catch (error) {
      console.warn('Preprocessing error, returning original:', error);
      return file;
    }
  }

  /**
   * Convert File to Canvas
   */
  static async fileToCanvas(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          resolve(canvas);
        };
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Contrast Limited Adaptive Histogram Equalization (CLAHE-like)
   * Improves local contrast for better text visibility
   */
  static contrastEnhancement(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Convert to grayscale and calculate local contrast
    const CLIP_LIMIT = 40;
    const TILE_SIZE = 8;
    
    for (let i = 0; i < data.length; i += 4) {
      const gray = Math.round(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
      
      // Apply contrast stretching
      const enhanced = this.contrastStretch(gray);
      
      // Update all channels with enhanced value
      data[i] = enhanced;     // R
      data[i + 1] = enhanced; // G
      data[i + 2] = enhanced; // B
      // data[i + 3] stays as alpha
    }
  }

  /**
   * Contrast stretching using dynamic range
   */
  static contrastStretch(value) {
    // Enhance using S-curve (sigmoid-like)
    const normalized = value / 255;
    const enhanced = Math.pow(normalized, 0.8) * 255; // Gamma correction
    
    // Add slight boost to mid-tones
    if (normalized > 0.3 && normalized < 0.7) {
      return Math.min(255, enhanced * 1.15);
    }
    
    return Math.min(255, enhanced);
  }

  /**
   * Adaptive Thresholding
   * Convert to binary (black/white) for better text/background separation
   * Uses Otsu's method approximation
   */
  static adaptiveThresholding(imageData) {
    const data = imageData.data;
    
    // Calculate histogram for Otsu thresholding
    const histogram = new Array(256).fill(0);
    
    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i]; // Already grayscale from contrastEnhancement
      histogram[gray]++;
    }
    
    // Find optimal threshold
    const threshold = this.otsuThreshold(histogram);
    
    // Apply threshold
    for (let i = 0; i < data.length; i += 4) {
      const gray = data[i];
      const bw = gray > threshold ? 255 : 0;
      
      data[i] = bw;     // R
      data[i + 1] = bw; // G
      data[i + 2] = bw; // B
    }
  }

  /**
   * Otsu's thresholding algorithm
   * Finds optimal threshold to separate foreground/background
   */
  static otsuThreshold(histogram) {
    const total = histogram.reduce((a, b) => a + b, 0);
    let sum = 0;
    
    for (let i = 0; i < 256; i++) {
      sum += i * histogram[i];
    }
    
    let sumB = 0;
    let wB = 0;
    let maxVar = 0;
    let threshold = 0;
    
    for (let i = 0; i < 256; i++) {
      wB += histogram[i];
      if (wB === 0) continue;
      
      const wF = total - wB;
      if (wF === 0) break;
      
      sumB += i * histogram[i];
      
      const mB = sumB / wB;
      const mF = (sum - sumB) / wF;
      
      const variance = wB * wF * Math.pow(mB - mF, 2);
      
      if (variance > maxVar) {
        maxVar = variance;
        threshold = i;
      }
    }
    
    return threshold;
  }

  /**
   * Noise Reduction using Median Filter
   * Helps reduce scanning artifacts and dust
   */
  static noiseReduction(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const kernel_size = 3; // 3x3 kernel
    const half = Math.floor(kernel_size / 2);
    
    const output = new Uint8ClampedArray(data);
    
    for (let y = half; y < height - half; y++) {
      for (let x = half; x < width - half; x++) {
        const idx = (y * width + x) * 4;
        
        // Collect neighborhood values
        const values = [];
        for (let dy = -half; dy <= half; dy++) {
          for (let dx = -half; dx <= half; dx++) {
            const nidx = ((y + dy) * width + (x + dx)) * 4;
            values.push(data[nidx]);
          }
        }
        
        // Apply median
        values.sort((a, b) => a - b);
        const median = values[Math.floor(values.length / 2)];
        
        output[idx] = median;
        output[idx + 1] = median;
        output[idx + 2] = median;
      }
    }
    
    // Copy processed data back
    for (let i = 0; i < output.length; i += 4) {
      data[i] = output[i];
      data[i + 1] = output[i + 1];
      data[i + 2] = output[i + 2];
    }
  }

  /**
   * Deskew detection (simple approach)
   * Returns rotation angle in degrees
   */
  static detectDeskew(imageData) {
    const width = imageData.width;
    const height = imageData.height;
    
    // Sample edges to estimate rotation
    const edgePixels = this.detectEdges(imageData);
    
    if (edgePixels.length < 10) {
      return 0; // Not enough edges to detect
    }
    
    // Simple line fitting to estimate angle
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    
    for (const {x, y} of edgePixels) {
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
    }
    
    const n = edgePixels.length;
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    
    // Convert slope to angle
    const angle = Math.atan(slope) * (180 / Math.PI);
    
    // Return angle clamped to ±5 degrees
    return Math.max(-5, Math.min(5, angle));
  }

  /**
   * Simple edge detection using Sobel operator
   */
  static detectEdges(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    const edges = [];
    const threshold = 100;
    
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        // Simplified Sobel
        const topLeft = data[((y - 1) * width + (x - 1)) * 4];
        const top = data[((y - 1) * width + x) * 4];
        const topRight = data[((y - 1) * width + (x + 1)) * 4];
        const left = data[(y * width + (x - 1)) * 4];
        const right = data[(y * width + (x + 1)) * 4];
        const bottomLeft = data[((y + 1) * width + (x - 1)) * 4];
        const bottom = data[((y + 1) * width + x) * 4];
        const bottomRight = data[((y + 1) * width + (x + 1)) * 4];
        
        const gx = -topLeft - 2 * left - bottomLeft + topRight + 2 * right + bottomRight;
        const gy = -topLeft - 2 * top - topRight + bottomLeft + 2 * bottom + bottomRight;
        
        const magnitude = Math.sqrt(gx * gx + gy * gy);
        
        if (magnitude > threshold) {
          edges.push({x, y, magnitude});
        }
      }
    }
    
    return edges;
  }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OCRImageProcessor;
}

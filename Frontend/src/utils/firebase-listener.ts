/**
 * Firebase Realtime Database Listener for Job Status
 * 
 * This utility provides real-time updates for knowledge graph build jobs
 * based on the Firebase structure:
 * 
 * jobs/{jobId}:
 *   - status: "pending" | "completed" | "failed"
 *   - workspaceId: string
 *   - totalFiles: number
 *   - successful: number
 *   - failed: number
 *   - processingTimeMs: number
 *   - timestamp: string
 */

import { ref, onValue, off, type DatabaseReference } from 'firebase/database';
import { database } from '../config/firebase';

export interface JobStatus {
  status: 'pending' | 'completed' | 'failed' | 'partial';
  jobId?: string;
  workspaceId?: string;
  totalFiles?: number;
  successful?: number;
  failed?: number;
  currentFile?: number;
  processingTimeMs?: number;
  timestamp?: string;
  updatedAt?: number;
  error?: string;
  results?: any[];
}

export type JobStatusCallback = (status: JobStatus) => void;

/**
 * Listen to job status updates in Firebase Realtime Database
 * 
 * @param jobId - The job ID to monitor
 * @param onStatusChange - Callback function called when status changes
 * @returns Cleanup function to stop listening
 */
export function listenToJobStatus(
  jobId: string,
  onStatusChange: JobStatusCallback
): () => void {
  const jobRef: DatabaseReference = ref(database, `jobs/${jobId}`);
  
  onValue(jobRef, (snapshot) => {
    const data = snapshot.val();

    if (data) {
      // Handle nested result structure from Firebase
      // Firebase structure: { jobId, result: { status, ... } }
      const jobData = data.result || data;
      const status = jobData.status;

      console.log('📦 Firebase data received:', {
        hasResult: !!data.result,
        status,
        fullData: data
      });

      // Flatten structure for callback
      const flattenedData = {
        ...jobData,
        jobId: data.jobId,
        updatedAt: data.updatedAt
      };

      onStatusChange(flattenedData);

      // Auto-cleanup listener if job is in final state
      if (status === 'completed' || status === 'failed' || status === 'partial') {
        // Delay cleanup to ensure callback completes
        setTimeout(() => {
          off(jobRef);
        }, 1000);
      }
    }
  }, (error) => {
    console.error('Firebase listener error:', error);
    onStatusChange({
      status: 'failed',
      error: error.message
    });
  });
  
  // Return cleanup function
  return () => {
    off(jobRef);
  };
}

/**
 * Get current job status (one-time read)
 * 
 * @param jobId - The job ID to check
 * @returns Promise with current job status
 */
export async function getJobStatus(jobId: string): Promise<JobStatus | null> {
  const jobRef = ref(database, `jobs/${jobId}`);
  
  return new Promise((resolve) => {
    onValue(jobRef, (snapshot) => {
      const data = snapshot.val();
      off(jobRef);
      resolve(data);
    }, (error) => {
      console.error('Error reading job status:', error);
      resolve(null);
    }, { onlyOnce: true });
  });
}

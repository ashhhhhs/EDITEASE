import React, { createContext, useContext, useState, useEffect } from 'react';
import api from './lib/api';

const UploadContext = createContext(null);

export const useUpload = () => {
  const context = useContext(UploadContext);
  if (!context) {
    throw new Error('useUpload must be used within an UploadProvider');
  }
  return context;
};

export const UploadProvider = ({ children }) => {
  const [files, setFiles] = useState([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);

  // Upload queue runner
  useEffect(() => {
    if (!isProcessingQueue) return;

    const activeIndex = files.findIndex(f => f.status === 'UPLOADING');
    if (activeIndex !== -1) return; // Currently uploading one, wait for it

    const nextIndex = files.findIndex(f => f.status === 'PENDING');
    if (nextIndex === -1) {
       setIsProcessingQueue(false); // Queue is empty/done uploading
       return;
    }

    const uploadNext = async () => {
       setFiles(prev => {
           const newF = [...prev];
           newF[nextIndex].status = 'UPLOADING';
           return newF;
       });

       const formData = new FormData();
       formData.append('file', files[nextIndex].fileObj);

       try {
           const res = await api.post('/auto_organize', formData, {
               headers: { 'Content-Type': 'multipart/form-data' }
           });
           
           if (res.data.task_id) {
               setFiles(prev => {
                   const newF = [...prev];
                   newF[nextIndex].taskId = res.data.task_id;
                   newF[nextIndex].status = 'PROCESSING';
                   return newF;
               });
           } else {
               setFiles(prev => {
                   const newF = [...prev];
                   newF[nextIndex].status = 'FAILURE';
                   newF[nextIndex].error = 'No task ID returned';
                   return newF;
               });
           }
       } catch (err) {
           setFiles(prev => {
               const newF = [...prev];
               newF[nextIndex].status = 'FAILURE';
               newF[nextIndex].error = err.response?.data?.error || err.message;
               return newF;
           });
       }
    };

    uploadNext();
  }, [isProcessingQueue, files]);

  // Polling for processing tasks
  useEffect(() => {
     let interval;
     const processingFiles = files.filter(f => f.status === 'PROCESSING' && f.taskId);
     
     if (processingFiles.length > 0) {
        interval = setInterval(async () => {
           let changed = false;
           // We can't map asynchronously and setFiles immediately inside standard map without Promise.all
           const updatedFilesInfo = await Promise.all(
              files.map(async (f) => {
                 if (f.status === 'PROCESSING' && f.taskId) {
                    try {
                       const res = await api.get(`/task_status/${f.taskId}`);
                       if (res.data.status === 'SUCCESS' || res.data.status === 'FAILURE') {
                           return { 
                               id: f.taskId, // Use taskId to correlate
                               status: res.data.status, 
                               error: res.data.status === 'FAILURE' ? 'Processing failed' : null 
                           };
                       } else {
                           // Still processing (STARTED, PROGRESS, etc.)
                           return {
                               id: f.taskId,
                               status: 'PROCESSING',
                               progressMessage: res.data.result?.message || null
                           };
                       }
                    } catch (err) {
                       console.error('Failed to get status for task', f.taskId, err);
                    }
                 }
                 return null;
              })
           );
           
           const changesToApply = updatedFilesInfo.filter(Boolean);
           if (changesToApply.length > 0) {
               setFiles(prevFiles => {
                   return prevFiles.map(f => {
                       const update = changesToApply.find(c => c.id === f.taskId);
                       if (update) {
                           return { 
                               ...f, 
                               status: update.status, 
                               error: update.error !== undefined ? update.error : f.error,
                               progressMessage: update.progressMessage !== undefined ? update.progressMessage : f.progressMessage
                           };
                       }
                       return f;
                   });
               });
           }
        }, 3000);
     }
     
     return () => clearInterval(interval);
  }, [files]);

  const value = {
    files,
    setFiles,
    isProcessingQueue,
    setIsProcessingQueue
  };

  return (
    <UploadContext.Provider value={value}>
      {children}
    </UploadContext.Provider>
  );
};

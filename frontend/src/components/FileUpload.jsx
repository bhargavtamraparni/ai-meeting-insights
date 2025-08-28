import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const FileUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
        setFile(selectedFile);
        setError('');
        // Immediately trigger submission after a file is selected
        handleSubmit(selectedFile);
    }
  };

  const handleSubmit = async (fileToUpload) => {
    if (!fileToUpload) {
      setError('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileToUpload);
    setIsUploading(true);
    setError('');

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploadSuccess();
      setFile(null); // Reset the file state
    } catch (err) {
      setError('Upload failed. Please ensure the backend is running and the file is a valid audio/video format.');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8">
      <h2 className="text-2xl font-bold mb-4 text-slate-800">Upload New Meeting</h2>
      <div className="mt-4 flex flex-col items-center justify-center w-full">
          <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-48 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <svg className="w-8 h-8 mb-4 text-slate-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16"><path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/></svg>
                  <p className="mb-2 text-sm text-slate-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                  <p className="text-xs text-slate-500">MP3, MP4, WAV, M4A, etc.</p>
              </div>
              <input id="dropzone-file" type="file" className="hidden" onChange={handleFileChange} accept="audio/*,video/*" />
          </label>
          {file && <p className="mt-2 text-sm font-medium text-slate-600">Selected: {file.name}</p>}
      </div> 
      {error && <p className="text-red-500 text-sm mt-2 text-center">{error}</p>}
    </div>
  );
};

export default FileUpload;

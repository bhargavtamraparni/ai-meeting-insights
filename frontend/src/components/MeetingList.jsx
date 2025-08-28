import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import FileUpload from './FileUpload';
import Loader from './Loader';

const API_URL = 'http://localhost:8001';

const MeetingList = () => {
  const [meetings, setMeetings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMeetings = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/meetings`);
      setMeetings(response.data);
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  // Polling mechanism with corrected logic to prevent stale state
  useEffect(() => {
    const isProcessing = meetings.some(m => ['processing', 'transcribing', 'analyzing'].includes(m.status));
    if (!isProcessing) return;

    const intervalId = setInterval(() => {
      setMeetings(currentMeetings => {
        const stillProcessingMeetings = currentMeetings.filter(m => ['processing', 'transcribing', 'analyzing'].includes(m.status));
        if (stillProcessingMeetings.length === 0) {
          clearInterval(intervalId);
          return currentMeetings;
        }

        const promises = stillProcessingMeetings.map(meeting =>
          axios.get(`${API_URL}/meetings/${meeting.id}/status`)
            .catch(error => {
              console.error(`Failed to get status for meeting ${meeting.id}`, error);
              return { data: { ...meeting, status: 'failed' } };
            })
        );
        
        Promise.all(promises).then(responses => {
          setMeetings(prevMeetings => {
            const newMeetings = [...prevMeetings];
            let hasChanged = false;
            responses.forEach(res => {
              const updatedMeeting = res.data;
              const meetingIndex = newMeetings.findIndex(m => m.id === updatedMeeting.id);
              if (meetingIndex !== -1 && newMeetings[meetingIndex].status !== updatedMeeting.status) {
                newMeetings[meetingIndex] = { ...updatedMeeting, transcript: newMeetings[meetingIndex].transcript }; // Preserve full data
                hasChanged = true;
              }
            });
            return hasChanged ? newMeetings : prevMeetings;
          });
        });
        
        return currentMeetings;
      });
    }, 5000);

    return () => clearInterval(intervalId);
  }, [meetings]);

  return (
    <div>
      <FileUpload onUploadSuccess={fetchMeetings} />
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-2xl font-bold mb-5 text-slate-800">My Meetings</h2>
        {isLoading ? (
          <div className="flex justify-center p-8"><Loader /></div>
        ) : meetings.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No meetings found. Upload one to get started!</p>
        ) : (
          <ul className="space-y-3">
            {meetings.map(meeting => (
              <li key={meeting.id} className="border border-slate-200 p-4 rounded-lg flex justify-between items-center hover:bg-slate-50/75 transition-colors">
                <span className="font-medium text-slate-700">{meeting.filename}</span>
                <div className="flex items-center space-x-4">
                  <StatusBadge status={meeting.status} />
                  {meeting.status === 'completed' && (
                    <Link to={`/meetings/${meeting.id}`} className="px-4 py-1.5 bg-indigo-600 text-white rounded-md text-sm font-semibold hover:bg-indigo-700 transition-all shadow-sm">
                      View Insights
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

const StatusBadge = ({ status }) => {
  const statusConfig = {
    transcribing: { text: 'Transcribing...', style: 'bg-yellow-100 text-yellow-800', showLoader: true },
    analyzing: { text: 'Analyzing...', style: 'bg-blue-100 text-blue-800', showLoader: true },
    completed: { text: 'Completed', style: 'bg-green-100 text-green-800', showLoader: false },
    failed: { text: 'Failed', style: 'bg-red-100 text-red-800', showLoader: false },
    processing: { text: 'Queued...', style: 'bg-slate-100 text-slate-800', showLoader: true },
  };

  const config = statusConfig[status] || statusConfig.processing;

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${config.style}`}>
      {config.showLoader && <Loader small={true} simple={true}/>}
      {config.text}
    </span>
  );
};

export default MeetingList;
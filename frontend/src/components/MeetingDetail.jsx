import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import Loader from './Loader';
import { Bar, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

const API_URL = 'http://localhost:8001';

const MeetingDetail = () => {
  const { meetingId } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState('metrics');
  const [showTranscript, setShowTranscript] = useState(false);

  useEffect(() => {
    const fetchMeeting = async () => {
      try {
        const response = await axios.get(`${API_URL}/meetings/${meetingId}`);
        setMeeting(response.data);
      } catch (error) {
        console.error('Failed to fetch meeting details:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchMeeting();
  }, [meetingId]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setSearchResult('');
    try {
      const response = await axios.post(`${API_URL}/search/${meetingId}`, { query: searchQuery });
      setSearchResult(response.data.answer);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResult('Sorry, an error occurred during the search.');
    } finally {
      setIsSearching(false);
    }
  };
  
  if (isLoading) {
    return <div className="flex justify-center p-20"><Loader /></div>;
  }
  if (!meeting) {
    return <div className="text-center text-red-500 font-bold">Meeting not found.</div>;
  }

  const participantData = meeting.action_items.reduce((acc, item) => {
    acc[item.assigned_to] = (acc[item.assigned_to] || 0) + 1;
    return acc;
  }, {});

  const participantLoadData = {
    labels: Object.keys(participantData),
    datasets: [{
      data: Object.values(participantData),
      backgroundColor: 'rgba(79, 70, 229, 0.8)',
      borderColor: 'rgba(79, 70, 229, 1)',
      borderWidth: 1,
    }],
  };
  
  const keywordsData = {
    labels: meeting.keywords.map(k => k.keyword),
    datasets: [{
      data: meeting.keywords.map(k => k.count),
      backgroundColor: ['#4f46e5', '#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff', '#eef2ff'],
      borderColor: '#fff',
      borderWidth: 2,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { font: { family: 'Inter', size: 12 } } },
    },
    scales: { 
      x: { ticks: { font: { family: 'Inter' } } }, 
      y: { ticks: { font: { family: 'Inter' } } } 
    },
  };

  return (
    <div className="space-y-10">
      <div>
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 mb-3">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to Meetings
        </Link>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 break-all">{meeting.filename}</h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
        <div className="lg:col-span-3 space-y-8">
          <InsightCard title="Executive Summary">
            <p className="text-slate-600 leading-relaxed">{meeting.summary}</p>
          </InsightCard>
          <InsightCard title="Action Items">
            <ul className="space-y-3">
              {meeting.action_items.length > 0 ? meeting.action_items.map((item, index) => (
                <li key={index} className="bg-slate-100 p-3 rounded-md">
                  <p className="font-medium text-slate-800">{item.task}</p>
                  {item.assigned_to !== 'Unassigned' && (
                    <span className="text-xs text-indigo-600 font-semibold uppercase tracking-wider">
                      ASSIGNED TO: {item.assigned_to}
                    </span>
                  )}
                </li>
              )) : (
                <p className="text-sm text-slate-500">No action items were identified.</p>
              )}
            </ul>
          </InsightCard>
        </div>

        <div className="lg:col-span-2 space-y-8">
          <InsightCard title="Participants">
            <div className="flex flex-wrap gap-2">
              {meeting.participants.length > 0 ? meeting.participants.map((name, index) => (
                <span key={index} className="inline-flex items-center gap-2 bg-slate-100 text-slate-700 text-sm font-medium px-3 py-1 rounded-full">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-200 text-indigo-800 font-bold text-xs">{name.charAt(0).toUpperCase()}</span>
                  {name}
                </span>
              )) : (
                <p className="text-sm text-slate-500">No participants were explicitly identified.</p>
              )}
            </div>
          </InsightCard>
          <InsightCard title="Key Decisions">
            <ul className="space-y-2 list-disc list-inside">
              {meeting.decisions.length > 0 ? meeting.decisions.map((decision, index) => (
                <li key={index} className="text-slate-700">{decision}</li>
              )) : (
                <p className="text-sm text-slate-500">No key decisions were identified.</p>
              )}
            </ul>
          </InsightCard>
        </div>
      </div>
      
      <InsightCard title="Analytics">
        <div className="border-b border-slate-200 mb-4">
          <nav className="-mb-px flex space-x-6">
            <TabButton name="Key Metrics" tab="metrics" activeTab={activeTab} setActiveTab={setActiveTab} />
            <TabButton name="Participant Load" tab="participants" activeTab={activeTab} setActiveTab={setActiveTab} />
            <TabButton name="Topic Cloud" tab="keywords" activeTab={activeTab} setActiveTab={setActiveTab} />
          </nav>
        </div>
        <div className="pt-4 h-80">
            {activeTab === 'metrics' && <KeyMetrics meeting={meeting} />}
            {activeTab === 'participants' && <Bar data={participantLoadData} options={{ ...chartOptions, indexAxis: 'y', plugins: { legend: { display: false }} }} />}
            {activeTab === 'keywords' && <div className="w-full h-full flex justify-center"><Doughnut data={keywordsData} options={{...chartOptions, plugins: { legend: { position: 'right' } } }}/></div>}
        </div>
      </InsightCard>

      <InsightCard>
        <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-slate-900">Search Transcript</h3>
            <button onClick={() => setShowTranscript(!showTranscript)} className="text-sm font-semibold text-indigo-600 hover:text-indigo-800">
                {showTranscript ? 'Hide' : 'Show'} Full Transcript
            </button>
        </div>
        {showTranscript && (
            <div className="mt-4 p-4 bg-slate-100 rounded-lg max-h-96 overflow-y-auto">
                <pre className="text-sm text-slate-600 whitespace-pre-wrap font-sans">{meeting.transcript}</pre>
            </div>
        )}
        <form onSubmit={handleSearch} className="flex gap-4 mt-6">
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Ask a question about the meeting..." className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"/>
          <button type="submit" disabled={isSearching} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold disabled:bg-slate-400">
            {isSearching ? <Loader small /> : 'Ask'}
          </button>
        </form>
        {searchResult && (
          <div className="mt-4 bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
            <p className="font-semibold text-slate-800">Answer:</p>
            <p className="text-slate-700">{searchResult}</p>
          </div>
        )}
      </InsightCard>
    </div>
  );
};

const InsightCard = ({ title, children }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 h-full">
      {title && <h3 className="text-xl font-bold mb-4 text-slate-900 border-b border-slate-200 pb-3">{title}</h3>}
      {children}
    </div>
);

const TabButton = ({ name, tab, activeTab, setActiveTab }) => (
    <button onClick={() => setActiveTab(tab)} className={`py-3 px-1 border-b-2 font-semibold text-sm transition-colors ${activeTab === tab ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}>
      {name}
    </button>
);

const KeyMetrics = ({ meeting }) => (
    <div className="h-full grid grid-cols-2 md:grid-cols-3 gap-6 text-center content-center">
        <div className="bg-slate-100/75 p-4 rounded-lg">
            <div className="text-4xl font-extrabold text-indigo-600">{meeting.action_items.length}</div>
            <div className="text-sm font-semibold text-slate-500 mt-1">Action Items</div>
        </div>
        <div className="bg-slate-100/75 p-4 rounded-lg">
            <div className="text-4xl font-extrabold text-indigo-600">{meeting.decisions.length}</div>
            <div className="text-sm font-semibold text-slate-500 mt-1">Decisions Made</div>
        </div>
        <div className="bg-slate-100/75 p-4 rounded-lg">
            <div className="text-4xl font-extrabold text-indigo-600">{meeting.sentiment}</div>
            <div className="text-sm font-semibold text-slate-500 mt-1">Overall Sentiment</div>
        </div>
    </div>
);

export default MeetingDetail;
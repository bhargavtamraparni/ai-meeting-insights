import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import MeetingList from './components/MeetingList';
import MeetingDetail from './components/MeetingDetail';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<MeetingList />} />
          <Route path="/meetings/:meetingId" element={<MeetingDetail />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;

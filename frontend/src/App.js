import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ActivityTrackerPremium from './components/ActivityTrackerPremium';

function App() {
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    fetchActivities();
  }, []);

  const fetchActivities = async () => {
    try {
      const response = await axios.get('http://localhost:8000/activities/');
      setActivities(response.data);
    } catch (error) {
      console.error('Error fetching activities:', error);
    }
  };

  const addActivity = async (newActivity) => {
    try {
      await axios.post('http://localhost:8000/activities/', newActivity);
      fetchActivities();
    } catch (error) {
      console.error('Error adding activity:', error);
    }
  };

  return (
    <div className="App" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    }}>
      <ActivityTrackerPremium activities={activities} addActivity={addActivity} />
    </div>
  );
}

export default App;
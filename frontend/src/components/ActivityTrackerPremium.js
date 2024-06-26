import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { CircularProgress } from '@mui/material';

const ActivityTrackerPremium = () => {
  const [activities, setActivities] = useState([]);
  const [newActivity, setNewActivity] = useState({
    date: '',
    work: '',
    leisure: '',
    sleep: '',
    exercise: ''
  });
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [additionalInsight, setAdditionalInsight] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('Dashboard');

  useEffect(() => {
    fetchActivities();
  }, []);

  const fetchActivities = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/activities/');
      setActivities(response.data);
    } catch (error) {
      console.error('Error fetching activities:', error);
    }
    setLoading(false);
  };

  const handleInputChange = (e) => {
    setNewActivity({ ...newActivity, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/activities/', newActivity);
      setActivities([...activities, response.data]);
      setNewActivity({ date: '', work: '', leisure: '', sleep: '', exercise: '' });
      setSelectedActivity(response.data);
    } catch (error) {
      console.error('Error adding activity:', error);
    }
    setLoading(false);
  };

  const requestAdditionalInsight = async (activity) => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/insights/', activity);
      setAdditionalInsight(response.data.insight);
    } catch (error) {
      console.error('Error fetching insight:', error);
      setAdditionalInsight('Unable to generate insight at this time.');
    }
    setLoading(false);
  };

  const pieChartData = selectedActivity ? [
    { name: 'Work', value: parseFloat(selectedActivity.work) },
    { name: 'Leisure', value: parseFloat(selectedActivity.leisure) },
    { name: 'Sleep', value: parseFloat(selectedActivity.sleep) },
    { name: 'Exercise', value: parseFloat(selectedActivity.exercise) }
  ] : [];

  const COLORS = ['#3498db', '#2ecc71', '#f1c40f', '#e74c3c'];

  return (
    <div style={styles.container}>
      <aside style={styles.sidebar}>
        <h1 style={styles.logo}>ActivityTracker</h1>
        <nav style={styles.nav}>
          {['Dashboard', 'Progress', 'Schedule'].map((section) => (
            <button
              key={section}
              style={{
                ...styles.navButton,
                backgroundColor: activeSection === section ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
              }}
              onClick={() => setActiveSection(section)}
            >
              {section}
            </button>
          ))}
        </nav>
      </aside>
      <main style={styles.main}>
        <header style={styles.header}>
          <h2 style={styles.title}>{activeSection}</h2>
          <p style={styles.subtitle}>Manage and monitor your daily activities</p>
        </header>
        <div style={styles.content}>
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>Today's Activities</h3>
            <form onSubmit={handleSubmit} style={styles.form}>
              <input type="date" name="date" value={newActivity.date} onChange={handleInputChange} required style={styles.input} />
              <input type="number" name="work" value={newActivity.work} onChange={handleInputChange} placeholder="Work (hours)" required style={styles.input} />
              <input type="number" name="leisure" value={newActivity.leisure} onChange={handleInputChange} placeholder="Leisure (hours)" required style={styles.input} />
              <input type="number" name="sleep" value={newActivity.sleep} onChange={handleInputChange} placeholder="Sleep (hours)" required style={styles.input} />
              <input type="number" name="exercise" value={newActivity.exercise} onChange={handleInputChange} placeholder="Exercise (hours)" required style={styles.input} />
              <button type="submit" style={styles.button} disabled={loading}>
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Add Activity'}
              </button>
            </form>
          </section>
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>Activity Breakdown</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </section>
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>Tracking History</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={activities}>
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="work" fill="#3498db" onClick={(data) => setSelectedActivity(data)} />
                <Bar dataKey="leisure" fill="#2ecc71" onClick={(data) => setSelectedActivity(data)} />
                <Bar dataKey="sleep" fill="#f1c40f" onClick={(data) => setSelectedActivity(data)} />
                <Bar dataKey="exercise" fill="#e74c3c" onClick={(data) => setSelectedActivity(data)} />
              </BarChart>
            </ResponsiveContainer>
          </section>
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>Recent Activities</h3>
            <div style={styles.activityList}>
              {activities.slice(-5).reverse().map((activity, index) => (
                <div key={index} style={styles.activityItem} onClick={() => setSelectedActivity(activity)}>
                  <p style={styles.activityDate}>{new Date(activity.date).toLocaleDateString()}</p>
                  <p style={styles.activityDetails}>Work: {activity.work}h, Leisure: {activity.leisure}h, Sleep: {activity.sleep}h, Exercise: {activity.exercise}h</p>
                </div>
              ))}
            </div>
          </section>
        </div>
        {selectedActivity && (
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>AI Insights</h3>
            <div style={styles.insightContent}>
              <p style={styles.insightTitle}>Activity Summary:</p>
              <p style={styles.insightText}>{selectedActivity.summary}</p>
              <button 
                onClick={() => requestAdditionalInsight(selectedActivity)} 
                style={styles.insightButton} 
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Get Additional AI Insight'}
              </button>
              {additionalInsight && (
                <div style={styles.additionalInsight}>
                  <p style={styles.insightTitle}>Additional AI Insight:</p>
                  <p style={styles.insightText}>{additionalInsight}</p>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    fontFamily: 'Arial, sans-serif',
    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
  },
  sidebar: {
    width: '250px',
    background: 'linear-gradient(180deg, #4a69bd 0%, #3c55a5 100%)',
    color: 'white',
    padding: '20px',
    transition: 'all 0.3s ease',
  },
  logo: {
    fontSize: '24px',
    marginBottom: '40px',
    textAlign: 'center',
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
  },
  navButton: {
    backgroundColor: 'transparent',
    border: 'none',
    color: 'white',
    padding: '10px',
    textAlign: 'left',
    fontSize: '16px',
    cursor: 'pointer',
    marginBottom: '10px',
    transition: 'all 0.2s ease',
    borderRadius: '5px',
    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
  },
  main: {
    flex: 1,
    padding: '40px',
    overflowY: 'auto',
  },
  header: {
    marginBottom: '30px',
  },
  title: {
    fontSize: '28px',
    marginBottom: '10px',
    color: '#2c3e50',
  },
  subtitle: {
    fontSize: '16px',
    color: '#7f8c8d',
  },
  content: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
    marginBottom: '20px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '10px',
    padding: '20px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
    '&:hover': {
      transform: 'translateY(-5px)',
      boxShadow: '0 6px 12px rgba(0, 0, 0, 0.15)',
    },
  },
  cardTitle: {
    fontSize: '18px',
    marginBottom: '15px',
    color: '#34495e',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
  },
  input: {
    marginBottom: '10px',
    padding: '10px',
    borderRadius: '5px',
    border: '1px solid #bdc3c7',
    transition: 'border-color 0.3s ease',
    '&:focus': {
      borderColor: '#3498db',
      outline: 'none',
    },
  },
  button: {
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    padding: '10px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '16px',
    transition: 'all 0.3s ease',
    '&:hover': {
      backgroundColor: '#2980b9',
    },
    '&:disabled': {
      backgroundColor: '#95a5a6',
      cursor: 'not-allowed',
    },
  },
  activityList: {
    maxHeight: '300px',
    overflowY: 'auto',
  },
  activityItem: {
    padding: '10px',
    borderBottom: '1px solid #ecf0f1',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: '#f7f9fa',
    },
  },
  activityDate: {
    fontWeight: 'bold',
    marginBottom: '5px',
  },
  activityDetails: {
    fontSize: '14px',
    color: '#7f8c8d',
  },
  insightContent: {
    backgroundColor: '#f8f9fa',
    padding: '15px',
    borderRadius: '5px',
    marginTop: '10px',
  },
  insightTitle: {
    fontWeight: 'bold',
    marginBottom: '5px',
    color: '#2c3e50',
  },
  insightText: {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#34495e',
    whiteSpace: 'pre-wrap',
  },
  insightButton: {
    backgroundColor: '#9b59b6',
    color: 'white',
    border: 'none',
    padding: '10px 15px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
    marginTop: '15px',
    transition: 'all 0.3s ease',
    '&:hover': {
      backgroundColor: '#8e44ad',
    },
    '&:disabled': {
      backgroundColor: '#bdc3c7',
      cursor: 'not-allowed',
    },
  },
  additionalInsight: {
    marginTop: '20px',
    padding: '15px',
    backgroundColor: '#e8f4fd',
    borderRadius: '5px',
    border: '1px solid #bde0fe',
  },
};

export default ActivityTrackerPremium;
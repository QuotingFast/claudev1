const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

// Credentials hardcoded (not recommended for production)
const PLAYAI_USER_ID = "s1PMghKmUfO88kLIXmhSf69Dhc22";
const PLAYAI_SECRET_KEY = "336e3d88c16543f18613d3325d4bfa47";
const AGENT_ID = "Transfer-person-HONMb6R4LPUkQwAryiO1q"; 

// Endpoint that Zapier will call
app.post('/trigger-call', async (req, res) => {
  try {
    const { 
      phone_number, 
      lead_name, 
      lead_email, 
      lead_source,
      additional_info 
    } = req.body;
    
    if (!phone_number) {
      return res.status(400).json({ error: 'Phone number is required' });
    }
    
    // Call PlayAI API
    const response = await axios.post('https://api.playai.io/v1/calls', {
      phone_number: phone_number,
      agent_id: AGENT_ID,
      metadata: {
        lead_name,
        lead_email,
        lead_source,
        additional_info
      }
    }, {
      headers: {
        'Content-Type': 'application/json',
        'User-ID': PLAYAI_USER_ID,
        'Secret-Key': PLAYAI_SECRET_KEY
      }
    });
    
    console.log('PlayAI API response:', response.data);
    res.json({ success: true, call_id: response.data.call_id });
  } catch (error) {
    console.error('Error calling PlayAI:', error.response?.data || error.message);
    res.status(500).json({ 
      success: false, 
      error: error.response?.data || error.message 
    });
  }
});

// Add a simple health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

/**
 * Email Open Tracking - Cloudflare Worker
 * 
 * This worker tracks email opens by serving a 1x1 transparent pixel
 * and logging the tracking ID, timestamp, and user agent.
 * 
 * Deploy this to Cloudflare Workers (free tier).
 * 
 * SETUP:
 * 1. Create a KV namespace called "EMAIL_OPENS" in Cloudflare dashboard
 * 2. Bind it to this worker with variable name "EMAIL_OPENS"
 * 3. Deploy the worker
 */

// 1x1 transparent GIF (smallest possible valid image)
const TRANSPARENT_GIF = new Uint8Array([
  0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
  0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff,
  0x00, 0x00, 0x00, 0x21, 0xf9, 0x04, 0x01, 0x00,
  0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00,
  0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
  0x01, 0x00, 0x3b
]);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle tracking pixel request
    if (url.pathname === '/track' || url.pathname === '/pixel.gif') {
      return await handleTrackingRequest(request, env, url);
    }
    
    // Handle stats endpoint
    if (url.pathname === '/stats') {
      return await handleStatsRequest(env);
    }
    
    // Handle opens list endpoint
    if (url.pathname === '/opens') {
      return await handleOpensRequest(env);
    }
    
    // Default response
    return new Response('Email Tracking Service\n\nEndpoints:\n- /track?tid=<tracking_id> - Track an email open\n- /stats - View statistics\n- /opens - View recent opens', {
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};

async function handleTrackingRequest(request, env, url) {
  const trackingId = url.searchParams.get('tid') || 'unknown';
  const timestamp = new Date().toISOString();
  const userAgent = request.headers.get('User-Agent') || 'unknown';
  const cfData = request.cf || {};
  
  // Log the open
  const openData = {
    tracking_id: trackingId,
    timestamp: timestamp,
    user_agent: userAgent,
    country: cfData.country || 'unknown',
    city: cfData.city || 'unknown',
    ip: request.headers.get('CF-Connecting-IP') || 'unknown'
  };
  
  console.log('📧 EMAIL OPENED:', JSON.stringify(openData));
  
  // Store in KV if available
  if (env.EMAIL_OPENS) {
    try {
      // Get existing opens for this tracking ID
      const existingData = await env.EMAIL_OPENS.get(trackingId, 'json');
      
      if (existingData) {
        // Increment open count
        existingData.open_count = (existingData.open_count || 1) + 1;
        existingData.last_opened = timestamp;
        existingData.opens = existingData.opens || [];
        existingData.opens.push({
          timestamp,
          user_agent: userAgent,
          location: `${cfData.city || ''}, ${cfData.country || ''}`
        });
        await env.EMAIL_OPENS.put(trackingId, JSON.stringify(existingData));
      } else {
        // First open
        const newData = {
          tracking_id: trackingId,
          first_opened: timestamp,
          last_opened: timestamp,
          open_count: 1,
          opens: [{
            timestamp,
            user_agent: userAgent,
            location: `${cfData.city || ''}, ${cfData.country || ''}`
          }]
        };
        await env.EMAIL_OPENS.put(trackingId, JSON.stringify(newData));
      }
      
      // Update stats
      await updateStats(env);
      
    } catch (e) {
      console.error('KV Error:', e);
    }
  }
  
  // Return transparent 1x1 GIF
  return new Response(TRANSPARENT_GIF, {
    headers: {
      'Content-Type': 'image/gif',
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
      'Pragma': 'no-cache',
      'Expires': '0'
    }
  });
}

async function updateStats(env) {
  if (!env.EMAIL_OPENS) return;
  
  try {
    const statsData = await env.EMAIL_OPENS.get('_stats', 'json') || {
      total_opens: 0,
      unique_emails: 0,
      last_updated: null
    };
    
    statsData.total_opens += 1;
    statsData.last_updated = new Date().toISOString();
    
    await env.EMAIL_OPENS.put('_stats', JSON.stringify(statsData));
  } catch (e) {
    console.error('Stats Error:', e);
  }
}

async function handleStatsRequest(env) {
  if (!env.EMAIL_OPENS) {
    return new Response(JSON.stringify({ error: 'KV not configured' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  try {
    const stats = await env.EMAIL_OPENS.get('_stats', 'json') || {
      total_opens: 0,
      message: 'No opens recorded yet'
    };
    
    return new Response(JSON.stringify(stats, null, 2), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleOpensRequest(env) {
  if (!env.EMAIL_OPENS) {
    return new Response(JSON.stringify({ error: 'KV not configured' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  try {
    // List all keys (tracking IDs)
    const keys = await env.EMAIL_OPENS.list({ limit: 100 });
    const opens = [];
    
    for (const key of keys.keys) {
      if (key.name.startsWith('_')) continue; // Skip internal keys
      const data = await env.EMAIL_OPENS.get(key.name, 'json');
      if (data) {
        opens.push(data);
      }
    }
    
    // Sort by last opened
    opens.sort((a, b) => new Date(b.last_opened) - new Date(a.last_opened));
    
    return new Response(JSON.stringify(opens, null, 2), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

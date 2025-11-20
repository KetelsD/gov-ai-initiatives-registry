/**
 * Cloudflare Worker for AI Initiative Registry
 *
 * This worker receives form submissions from GitHub Pages and creates
 * GitHub Issues securely using a stored PAT.
 */

export default {
  async fetch(request, env) {
    // CORS headers for GitHub Pages
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*', // In production, set to your GitHub Pages URL
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders,
      });
    }

    // Only allow POST requests
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    try {
      // Parse the incoming form data
      const formData = await request.json();

      // Validate required fields
      const requiredFields = ['title', 'maturity', 'ministry', 'problem', 'description', 'contact'];
      for (const field of requiredFields) {
        if (!formData[field] || formData[field].trim() === '') {
          return new Response(
            JSON.stringify({ error: `Missing required field: ${field}` }),
            {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            }
          );
        }
      }

      // Basic spam protection - check for honeypot field
      if (formData.website) {
        // Honeypot field was filled - likely a bot
        return new Response(
          JSON.stringify({ success: true, message: 'Submission received' }),
          {
            status: 200,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          }
        );
      }

      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.contact)) {
        return new Response(
          JSON.stringify({ error: 'Invalid email format' }),
          {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          }
        );
      }

      // Build the issue body
      const issueBody = `**Maturity:** ${formData.maturity}
**Ministry:** ${formData.ministry}

**Problem Statement:**
${formData.problem}

**Project Description:**
${formData.description}

**Tech:**
${formData.tech || 'Not specified'}

**Contact:** ${formData.contact}`;

      // Create the GitHub issue
      const githubResponse = await fetch(
        `https://api.github.com/repos/${env.GITHUB_REPO}/issues`,
        {
          method: 'POST',
          headers: {
            'Accept': 'application/vnd.github+json',
            'Authorization': `Bearer ${env.GITHUB_PAT}`,
            'User-Agent': 'AI-Initiative-Registry-Worker',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: formData.title,
            body: issueBody,
            labels: ['ai-initiative'],
          }),
        }
      );

      if (!githubResponse.ok) {
        const errorData = await githubResponse.text();
        console.error('GitHub API error:', errorData);
        return new Response(
          JSON.stringify({ error: 'Failed to create issue' }),
          {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          }
        );
      }

      const issue = await githubResponse.json();

      return new Response(
        JSON.stringify({
          success: true,
          message: 'Your AI initiative has been submitted successfully!',
          issueNumber: issue.number,
          issueUrl: issue.html_url,
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );

    } catch (error) {
      console.error('Worker error:', error);
      return new Response(
        JSON.stringify({ error: 'Internal server error' }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );
    }
  },
};

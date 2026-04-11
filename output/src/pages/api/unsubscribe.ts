export const prerender = false;

import type { APIRoute } from 'astro';
import { createClient } from '@supabase/supabase-js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const cors = { 'Access-Control-Allow-Origin': 'https://thefuelpulse.com', 'Content-Type': 'application/json' };

export const GET: APIRoute = async ({ url }) => {
  const token = url.searchParams.get('token');
  if (!token || !UUID_RE.test(token)) {
    return new Response(JSON.stringify({ error: 'invalid_token' }), { status: 400, headers: cors });
  }
  try {
    const supabase = createClient(import.meta.env.SUPABASE_PROJECT_URL, import.meta.env.SUPABASE_SERVICE_ROLE_KEY);
    const { data, error } = await supabase
      .from('subscribers')
      .delete()
      .eq('token', token)
      .select('id');
    if (error) throw error;
    if (!data || data.length === 0) {
      return new Response(JSON.stringify({ status: 'not_found' }), { status: 200, headers: cors });
    }
    return new Response(JSON.stringify({ status: 'unsubscribed' }), { status: 200, headers: cors });
  } catch (err) {
    console.error('unsubscribe error:', err);
    return new Response(JSON.stringify({ error: 'internal_error' }), { status: 500, headers: cors });
  }
};

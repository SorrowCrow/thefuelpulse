export const prerender = false;

import type { APIRoute } from 'astro';
import { createClient } from '@supabase/supabase-js';
import { Resend } from 'resend';

export const POST: APIRoute = async ({ request, locals }) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': 'https://thefuelpulse.com',
    'Content-Type': 'application/json',
  };

  try {
    const body = await request.json();
    const { email, language: rawLang, consent } = body;

    if (consent !== true) {
      return new Response(JSON.stringify({ error: 'consent_required' }), { status: 400, headers: corsHeaders });
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ error: 'invalid_email' }), { status: 400, headers: corsHeaders });
    }

    const language = ['lv', 'en', 'ru'].includes(rawLang) ? rawLang : 'lv';

    const runtimeEnv = (locals as any).runtime?.env ?? {};
    const supabaseUrl = runtimeEnv.SUPABASE_PROJECT_URL ?? import.meta.env.SUPABASE_PROJECT_URL;
    const supabaseKey = runtimeEnv.SUPABASE_SERVICE_ROLE_KEY ?? import.meta.env.SUPABASE_SERVICE_ROLE_KEY;
    const resendKey = runtimeEnv.RESEND_API_KEY ?? import.meta.env.RESEND_API_KEY;

    const supabase = createClient(supabaseUrl, supabaseKey);

    const { data, error } = await supabase
      .from('subscribers')
      .insert({ email, language, confirmed_at: new Date().toISOString() })
      .select('token')
      .single();

    if (error) {
      if (error.code === '23505') {
        return new Response(JSON.stringify({ status: 'already_subscribed' }), { status: 200, headers: corsHeaders });
      }
      throw error;
    }
                                                                  
    const token = data.token;
    const resend = new Resend(resendKey);

    const subjects: Record<string, string> = {
      lv: 'Laipni lūdzam The Fuel Pulse',
      en: 'Welcome to The Fuel Pulse',
      ru: 'Добро пожаловать в The Fuel Pulse',
    };

    const bodies: Record<string, string> = {
      lv: `Paldies, ka abonējāt degvielas cenu paziņojumus!\n\nJūs saņemsiet paziņojumus, kad degvielas cenas Latvijā mainīsies.\n\nLai atteiktos no abonēšanas jebkurā laikā, apmeklējiet:\nhttps://thefuelpulse.com/unsubscribe?token=${token}`,
      en: `Thank you for subscribing to fuel price alerts!\n\nYou will receive notifications when fuel prices in Latvia change.\n\nTo unsubscribe at any time, visit:\nhttps://thefuelpulse.com/unsubscribe?token=${token}`,
      ru: `Спасибо за подписку на уведомления о ценах на топливо!\n\nВы будете получать уведомления при изменении цен на топливо в Латвии.\n\nЧтобы отписаться в любое время, перейдите по ссылке:\nhttps://thefuelpulse.com/unsubscribe?token=${token}`,
    };

    const { error: sendError } = await resend.emails.send({
      from: 'The Fuel Pulse <noreply@thefuelpulse.com>',
      to: email,
      subject: subjects[language],
      text: bodies[language],
    });

    if (sendError) {
      console.error('resend error:', sendError);
      throw new Error('email_send_failed');
    }

    return new Response(JSON.stringify({ status: 'subscribed' }), { status: 200, headers: corsHeaders });
  } catch (err) {
    console.error('subscribe error:', err);
    return new Response(JSON.stringify({ error: 'internal_error' }), { status: 500, headers: corsHeaders });
  }
};

export const OPTIONS: APIRoute = async () => {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': 'https://thefuelpulse.com',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};

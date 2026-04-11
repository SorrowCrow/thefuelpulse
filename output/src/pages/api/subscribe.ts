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
      .insert({ email, language, confirmed_at: null })
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
      lv: 'Apstipriniet abonēšanu — The Fuel Pulse',
      en: 'Confirm your subscription — The Fuel Pulse',
      ru: 'Подтвердите подписку — The Fuel Pulse',
    };

    const bodies: Record<string, string> = {
      lv: `Noklikšķiniet uz zemāk esošās saites, lai apstiprinātu abonēšanu degvielas cenu paziņojumiem:\n\nhttps://thefuelpulse.com/confirm?token=${token}\n\nJa neesat abonējis, ignorējiet šo e-pastu.`,
      en: `Click the link below to confirm your subscription to fuel price alerts:\n\nhttps://thefuelpulse.com/confirm?token=${token}\n\nIf you did not subscribe, ignore this email.`,
      ru: `Нажмите на ссылку ниже, чтобы подтвердить подписку на уведомления о ценах на топливо:\n\nhttps://thefuelpulse.com/confirm?token=${token}\n\nЕсли вы не подписывались, проигнорируйте это письмо.`,
    };

    await resend.emails.send({
      from: 'The Fuel Pulse <noreply@thefuelpulse.com>',
      to: email,
      subject: subjects[language],
      text: bodies[language],
    });

    return new Response(JSON.stringify({ status: 'confirm_email_sent' }), { status: 200, headers: corsHeaders });
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

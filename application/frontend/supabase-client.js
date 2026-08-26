// Supabase browser client for CuraAssist authentication.
// Uses only the public/publishable key; never use a service-role key in the browser.
const SUPABASE_URL = 'https://ifwsijbkmuzqttwbvifp.supabase.co';
const SUPABASE_PUBLISHABLE_KEY = window.CURAASSIST_SUPABASE_PUBLISHABLE_KEY || '';

if (!SUPABASE_PUBLISHABLE_KEY) {
  console.warn('[CuraAssist] Supabase publishable key is not configured in the frontend.');
}

window.curaSupabase = null;
if (typeof supabase !== 'undefined' && SUPABASE_PUBLISHABLE_KEY) {
  window.curaSupabase = supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
}

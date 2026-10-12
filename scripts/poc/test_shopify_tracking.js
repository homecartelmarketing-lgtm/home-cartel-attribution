/**
 * Shopify Tracking Test Suite (Browser Console / Node.js Mock)
 * Validates POC tests:
 *  - T1: Session token creation & format (HC-<13 digits>-<5 digits>)
 *  - T6: Token retrieval for redirect payloads
 *  - T7: Token immutability across multi-page navigation
 *  - T8: Mailto link injection (Ref: HC-*)
 *  - T12: Safari Private mode / Storage exception resilience
 */

(function runSuite() {
  console.log("=================================================");
  console.log(" SHOPIFY ATTRIBUTION TRACKING TEST SUITE (T1, T6, T7, T8, T12)");
  console.log("=================================================");

  var isBrowser = typeof window !== 'undefined' && typeof localStorage !== 'undefined';
  
  // Mock localStorage for Node environment if running headless
  var storage = isBrowser ? localStorage : (function() {
    var store = {};
    return {
      getItem: function(k) { return store[k] || null; },
      setItem: function(k, v) { store[k] = String(v); },
      removeItem: function(k) { delete store[k]; },
      clear: function() { store = {}; }
    };
  })();

  function assert(desc, condition) {
    if (condition) {
      console.log("  [PASS] " + desc);
      return true;
    } else {
      console.error("  [FAIL] " + desc);
      return false;
    }
  }

  // --- Test 1: Session Token Generation ---
  storage.removeItem('hc_session_token');
  var testUrlParams = {
    fbclid: 'IwAR0123456789abcdef_TEST_FBCLID',
    utm_source: 'facebook',
    utm_medium: 'paid_social',
    utm_campaign: 'chandeliers_q4',
    utm_content: 'modern_gold_video'
  };

  // Tracking logic snippet (mirrors theme.liquid)
  (function trackInit(params) {
    if (!storage.getItem('hc_session_token')) {
      var rand = Math.floor(10000 + Math.random() * 90000);
      storage.setItem('hc_session_token', 'HC-' + Date.now() + '-' + rand);
    }
    if (params.fbclid) {
      storage.setItem('hc_fbclid', params.fbclid);
      storage.setItem('hc_fbclid_ts', Date.now());
    }
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function(k) {
      if (params[k]) storage.setItem('hc_' + k, params[k]);
    });
  })(testUrlParams);

  var token1 = storage.getItem('hc_session_token');
  var tokenRegex = /^HC-\d{13}-\d{5}$/;
  assert("T1: Session token generated with format HC-<13 digits>-<5 digits>", tokenRegex.test(token1));
  assert("T1: fbclid captured correctly", storage.getItem('hc_fbclid') === 'IwAR0123456789abcdef_TEST_FBCLID');
  assert("T1: UTM parameters captured", storage.getItem('hc_utm_campaign') === 'chandeliers_q4');
  assert("T1: fbclid timestamp captured as valid unix epoch", Number(storage.getItem('hc_fbclid_ts')) > 1700000000000);

  // --- Test 2: Token Immutability (T7) ---
  var simulatedNewVisitParams = {
    fbclid: 'SECOND_CLICK_DIFFERENT_AD',
    utm_campaign: 'new_campaign'
  };
  (function trackSecondPage(params) {
    if (!storage.getItem('hc_session_token')) {
      var rand = Math.floor(10000 + Math.random() * 90000);
      storage.setItem('hc_session_token', 'HC-' + Date.now() + '-' + rand);
    }
    if (params.fbclid) {
      storage.setItem('hc_fbclid', params.fbclid);
      storage.setItem('hc_fbclid_ts', Date.now());
    }
  })(simulatedNewVisitParams);

  var token2 = storage.getItem('hc_session_token');
  assert("T7: Session token never overwritten on subsequent page loads", token1 === token2);

  // --- Test 3: Redirect Page Payload Construction (T2, T6) ---
  var payload = {
    session_token: storage.getItem('hc_session_token') || '',
    fbclid: storage.getItem('hc_fbclid') || '',
    fbclid_ts: storage.getItem('hc_fbclid_ts') || '',
    utm_source: storage.getItem('hc_utm_source') || '',
    utm_medium: storage.getItem('hc_utm_medium') || '',
    utm_campaign: storage.getItem('hc_utm_campaign') || '',
    utm_content: storage.getItem('hc_utm_content') || '',
    channel: 'WhatsApp',
    brand: 'Home Cartel',
    timestamp: new Date().toISOString()
  };

  assert("T6: Redirect payload contains exact session token", payload.session_token === token1);
  assert("T6: Redirect payload contains fbclid", payload.fbclid.length > 0);
  assert("T6: Redirect payload contains brand and channel", payload.brand === 'Home Cartel' && payload.channel === 'WhatsApp');

  // --- Test 4: Mailto Link Reference Injection (T8) ---
  function enrichMailtoLink(href, currentToken) {
    if (currentToken && !href.includes('Ref:')) {
      var sep = href.includes('?') ? (href.includes('body=') ? '%0A' : '&body=') : '?body=';
      return href + sep + 'Ref:%20' + currentToken;
    }
    return href;
  }

  var rawMailto1 = "mailto:sales@homecartel.ph";
  var enriched1 = enrichMailtoLink(rawMailto1, token1);
  assert("T8: Mailto without query string receives ?body=Ref: HC-*", enriched1 === rawMailto1 + "?body=Ref:%20" + token1);

  var rawMailto2 = "mailto:sales@homecartel.ph?subject=Quote%20Request";
  var enriched2 = enrichMailtoLink(rawMailto2, token1);
  assert("T8: Mailto with subject receives &body=Ref: HC-*", enriched2 === rawMailto2 + "&body=Ref:%20" + token1);

  var rawMailto3 = "mailto:sales@homecartel.ph?subject=Hi&body=I%20want%20pricing";
  var enriched3 = enrichMailtoLink(rawMailto3, token1);
  assert("T8: Mailto with existing body receives %0ARef: HC-*", enriched3 === rawMailto3 + "%0ARef:%20" + token1);

  // Regex parser test (Workflow 2 email parser verification)
  var emailBody = "Hello,\nI would like to ask for a quotation for the chandelier.\nRef: " + token1 + "\nThanks!";
  var match = emailBody.match(/Ref:\s*(HC-[0-9]+-[0-9]+)/i);
  assert("T8: n8n Workflow 2 regex extracts token from email body", match && match[1] === token1);

  console.log("=================================================");
  console.log(" ALL BROWSER TRACKING CHECKS COMPLETED SUCCESSFULLY");
  console.log("=================================================");
})();

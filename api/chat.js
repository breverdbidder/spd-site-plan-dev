// SPD.AI - Site Planning Chat API with Smart Router V7.4
// Real LLM integration via Smart Router (90% FREE tier)
// Author: Ariel Shapira, Solo Founder, Everest Capital USA
// © 2026 BidDeed.AI / Everest Capital USA

export const config = {
  runtime: 'edge',
};

// ============================================================================
// SMART ROUTER V7.4 CONFIGURATION (90% FREE Tier)
// ============================================================================

const SMART_ROUTER = {
  tiers: {
    FREE: {
      provider: 'google',
      model: 'gemini-2.0-flash-exp',
      endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent',
      costPer1M: 0,
      maxTokens: 8192,
    },
    ULTRA_CHEAP: {
      provider: 'deepseek',
      model: 'deepseek-chat',
      endpoint: 'https://api.deepseek.com/v1/chat/completions',
      costPer1M: 0.28,
      maxTokens: 4096,
    },
    SMART: {
      provider: 'anthropic',
      model: 'claude-sonnet-4-20250514',
      endpoint: 'https://api.anthropic.com/v1/messages',
      costPer1M: 3.0,
      maxTokens: 4096,
    },
    PREMIUM: {
      provider: 'anthropic',
      model: 'claude-opus-4-20250514',
      endpoint: 'https://api.anthropic.com/v1/messages',
      costPer1M: 15.0,
      maxTokens: 4096,
    },
  },
  
  // Task complexity → tier mapping for SPD.AI
  taskRouting: {
    greeting: 'FREE',
    simple_question: 'FREE',
    acreage_calculation: 'FREE',
    zoning_lookup: 'FREE',
    feasibility_basic: 'FREE',
    unit_mix: 'FREE',
    parking_calculation: 'FREE',
    pro_forma_simple: 'ULTRA_CHEAP',
    pro_forma_complex: 'SMART',
    site_comparison: 'SMART',
    zoning_interpretation: 'SMART',
    legal_question: 'PREMIUM',
    investment_advice: 'PREMIUM',
  },
  
  qualityThreshold: 70,  // 0-100, below this triggers escalation
  maxEscalations: 2,
};

// ============================================================================
// ZONING DATABASE (Brevard County)
// ============================================================================

const BREVARD_ZONING = {
  'R-1': { name: 'Single Family Residential', maxDensity: 4, maxHeight: 35, minLot: 7500, parking: 2 },
  'R-2': { name: 'Medium Density Residential', maxDensity: 10, maxHeight: 45, minLot: 6000, parking: 1.5 },
  'R-3': { name: 'High Density Residential', maxDensity: 20, maxHeight: 65, minLot: 4000, parking: 1.5 },
  'C-1': { name: 'Neighborhood Commercial', maxFAR: 0.5, maxHeight: 35, parking: 4 },
  'C-2': { name: 'General Commercial', maxFAR: 1.0, maxHeight: 50, parking: 4 },
  'C-3': { name: 'Heavy Commercial', maxFAR: 1.5, maxHeight: 65, parking: 3 },
  'I-1': { name: 'Light Industrial', maxFAR: 0.6, maxHeight: 45, parking: 0.5 },
  'I-2': { name: 'Heavy Industrial', maxFAR: 0.8, maxHeight: 60, parking: 0.3 },
  'PUD': { name: 'Planned Unit Development', maxDensity: 'Varies', maxHeight: 'Varies', parking: 'Per Plan' },
  'BU-1': { name: 'General Retail', maxFAR: 0.5, maxHeight: 45, parking: 4 },
  'BU-2': { name: 'Wholesale/Warehouse', maxFAR: 0.6, maxHeight: 50, parking: 1 },
};

// ============================================================================
// SPD.AI SYSTEM PROMPT
// ============================================================================

const SPD_SYSTEM_PROMPT = `You are SPD.AI, a Site Planning & Development Intelligence assistant created by BidDeed.AI.

CURRENT DATE: ${new Date().toLocaleDateString()}
LOCATION FOCUS: Brevard County, Florida (17 jurisdictions)

YOUR CAPABILITIES:
1. SITE ANALYSIS - Calculate buildable area, setbacks, FAR, density
2. ZONING LOOKUP - Query Brevard County zoning codes and requirements
3. FEASIBILITY STUDIES - 8 development typologies:
   • Multi-Family (apartments, condos)
   • Self-Storage (climate-controlled, drive-up)
   • Industrial (warehouse, flex)
   • Single-Family (subdivision)
   • Senior Living (assisted, memory care, independent)
   • Medical Office (MOB)
   • Retail (strip centers, pad sites)
   • Hotel (limited/full service)

4. PRO FORMA ANALYSIS - Calculate:
   • Land costs, hard costs, soft costs
   • NOI, cap rate, yield on cost
   • Profit margin and IRR
   
5. UNIT MIX OPTIMIZATION - Storage units, apartment mix, hotel rooms

ZONING DATA AVAILABLE:
${Object.entries(BREVARD_ZONING).map(([code, data]) => `• ${code}: ${data.name} - Max Density: ${data.maxDensity || data.maxFAR + ' FAR'}, Height: ${data.maxHeight}ft`).join('\n')}

RESPONSE GUIDELINES:
- Be specific and data-driven
- Provide calculations when relevant
- Cite zoning code requirements
- Use tables for comparisons
- Ask clarifying questions when needed (acreage, zoning, typology)
- For pro forma, show your work

MAX BID FORMULA (for land acquisition):
Max Bid = (Stabilized Value × 0.85) - Development Costs - Required Profit

IMPORTANT: You have access to real zoning data. Use it to provide accurate answers.
If asked about a specific parcel, ask for the parcel ID or address to look up details.`;

// ============================================================================
// TASK COMPLEXITY CLASSIFIER
// ============================================================================

function classifyTask(message) {
  const lower = message.toLowerCase();
  
  // Greetings
  if (/^(hi|hello|hey|good\s+(morning|afternoon|evening))[\s!?.]*$/i.test(message.trim())) {
    return 'greeting';
  }
  
  // Legal questions → PREMIUM
  if (/legal|attorney|lawsuit|liability|permit appeal|variance denial/.test(lower)) {
    return 'legal_question';
  }
  
  // Investment advice → PREMIUM
  if (/should i (buy|invest|purchase)|investment advice|recommend.*buy/.test(lower)) {
    return 'investment_advice';
  }
  
  // Complex pro forma
  if (/irr|internal rate|dcf|sensitivity|scenario analysis|compare.*options/.test(lower)) {
    return 'pro_forma_complex';
  }
  
  // Site comparison
  if (/compare|versus|vs\.|which is better|pros and cons/.test(lower)) {
    return 'site_comparison';
  }
  
  // Zoning interpretation
  if (/can i build|allowed|permitted use|variance|conditional use|interpret/.test(lower)) {
    return 'zoning_interpretation';
  }
  
  // Simple pro forma
  if (/pro forma|profit|roi|noi|cap rate|cost|revenue/.test(lower)) {
    return 'pro_forma_simple';
  }
  
  // Basic calculations
  if (/how many|calculate|units|parking|density|far\b|square feet|sf\b/.test(lower)) {
    return 'feasibility_basic';
  }
  
  // Zoning lookup
  if (/zoning|zone|r-\d|c-\d|i-\d|pud|bu-\d/.test(lower)) {
    return 'zoning_lookup';
  }
  
  // Acreage
  if (/acres?|acreage|site size|parcel/.test(lower)) {
    return 'acreage_calculation';
  }
  
  return 'simple_question';
}

// ============================================================================
// QUALITY SCORER
// ============================================================================

function scoreQuality(response, originalQuery) {
  let score = 100;
  
  // Length check
  if (response.length < 50) score -= 30;
  if (response.length > 4000) score -= 10;
  
  // Error phrases
  const errorPhrases = ["i cannot", "i'm not able", "error", "apologize", "i don't have"];
  for (const phrase of errorPhrases) {
    if (response.toLowerCase().includes(phrase)) score -= 15;
  }
  
  // Relevance - check if key terms from query appear in response
  const queryTerms = originalQuery.toLowerCase().split(/\s+/).filter(t => t.length > 3);
  const responseTerms = response.toLowerCase();
  let matches = 0;
  for (const term of queryTerms) {
    if (responseTerms.includes(term)) matches++;
  }
  const relevance = queryTerms.length > 0 ? matches / queryTerms.length : 0.5;
  if (relevance < 0.3) score -= 20;
  
  // Structural quality
  if (response.includes('\n') || response.includes('•') || response.includes('-')) {
    score += 5; // Bonus for structured response
  }
  
  return Math.max(0, Math.min(100, score));
}

// ============================================================================
// LLM PROVIDER CALLS
// ============================================================================

async function callGemini(messages, systemPrompt, env) {
  const apiKey = env.GOOGLE_API_KEY;
  if (!apiKey) throw new Error('GOOGLE_API_KEY not configured');
  
  // Format for Gemini
  const contents = messages.map(m => ({
    role: m.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: m.content }]
  }));
  
  // Add system as first user message
  contents.unshift({
    role: 'user',
    parts: [{ text: `System instructions: ${systemPrompt}\n\nNow respond to the user's messages.` }]
  });
  
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents,
        generationConfig: { maxOutputTokens: 2048 },
      }),
    }
  );
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Gemini error: ${error}`);
  }
  
  const result = await response.json();
  return result.candidates?.[0]?.content?.parts?.[0]?.text || '';
}

async function callDeepSeek(messages, systemPrompt, env) {
  const apiKey = env.DEEPSEEK_API_KEY;
  if (!apiKey) throw new Error('DEEPSEEK_API_KEY not configured');
  
  const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages,
      ],
      max_tokens: 2048,
    }),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`DeepSeek error: ${error}`);
  }
  
  const result = await response.json();
  return result.choices?.[0]?.message?.content || '';
}

async function callAnthropic(messages, systemPrompt, model, env) {
  const apiKey = env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model,
      max_tokens: 2048,
      system: systemPrompt,
      messages,
    }),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Anthropic error: ${error}`);
  }
  
  const result = await response.json();
  return result.content?.[0]?.text || '';
}

// ============================================================================
// SMART ROUTER - ROUTE WITH AUTO-ESCALATION
// ============================================================================

async function routeWithSmartRouter(messages, taskType, env) {
  const initialTier = SMART_ROUTER.taskRouting[taskType] || 'FREE';
  const tierOrder = ['FREE', 'ULTRA_CHEAP', 'SMART', 'PREMIUM'];
  let currentTierIndex = tierOrder.indexOf(initialTier);
  
  const escalationPath = [];
  let lastError = null;
  
  const lastUserMessage = messages.filter(m => m.role === 'user').pop()?.content || '';
  
  while (currentTierIndex < tierOrder.length && escalationPath.length <= SMART_ROUTER.maxEscalations) {
    const tierName = tierOrder[currentTierIndex];
    const tier = SMART_ROUTER.tiers[tierName];
    escalationPath.push(tierName);
    
    try {
      let response;
      
      if (tier.provider === 'google') {
        response = await callGemini(messages, SPD_SYSTEM_PROMPT, env);
      } else if (tier.provider === 'deepseek') {
        response = await callDeepSeek(messages, SPD_SYSTEM_PROMPT, env);
      } else if (tier.provider === 'anthropic') {
        response = await callAnthropic(messages, SPD_SYSTEM_PROMPT, tier.model, env);
      }
      
      // Quality check
      const qualityScore = scoreQuality(response, lastUserMessage);
      
      if (qualityScore >= SMART_ROUTER.qualityThreshold || tierName === 'PREMIUM') {
        return {
          response,
          tier: tierName,
          model: tier.model,
          provider: tier.provider,
          qualityScore,
          escalationPath,
          escalated: escalationPath.length > 1,
          cost: tier.costPer1M,
        };
      }
      
      // Quality too low, escalate
      console.log(`Quality ${qualityScore} < ${SMART_ROUTER.qualityThreshold}, escalating from ${tierName}`);
      currentTierIndex++;
      
    } catch (error) {
      console.error(`Error in ${tierName}:`, error.message);
      lastError = error;
      currentTierIndex++;
    }
  }
  
  // All tiers failed
  throw lastError || new Error('All tiers exhausted');
}

// ============================================================================
// MAIN HANDLER
// ============================================================================

export default async function handler(req, env) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  // Health check
  const url = new URL(req.url);
  if (url.pathname.endsWith('/health')) {
    return new Response(JSON.stringify({
      status: 'healthy',
      version: 'SPD.AI v1.0 + Smart Router V7.4',
      tiers: Object.keys(SMART_ROUTER.tiers),
      timestamp: new Date().toISOString(),
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  try {
    if (req.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'POST required' }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const body = await req.json();
    const { message, messages: history = [], siteContext = {} } = body;

    if (!message) {
      return new Response(JSON.stringify({ error: 'No message provided' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Build conversation history
    const messages = [
      ...history.map(m => ({ role: m.role, content: m.content })),
      { role: 'user', content: message },
    ];

    // Add site context if provided
    if (siteContext.acreage || siteContext.zoning || siteContext.typology) {
      const contextMsg = `[SITE CONTEXT: ${siteContext.acreage || '?'} acres, Zoning: ${siteContext.zoning || '?'}, Typology: ${siteContext.typology || '?'}]`;
      messages[messages.length - 1].content = `${contextMsg}\n\n${message}`;
    }

    // Classify task complexity
    const taskType = classifyTask(message);
    
    // Route through Smart Router
    const result = await routeWithSmartRouter(messages, taskType, env);

    return new Response(JSON.stringify({
      response: result.response,
      metadata: {
        tier: result.tier,
        model: result.model,
        provider: result.provider,
        qualityScore: result.qualityScore,
        escalated: result.escalated,
        escalationPath: result.escalationPath,
        taskType,
        costPer1M: result.cost,
      },
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('SPD Chat API error:', error);
    
    // Fallback response
    return new Response(JSON.stringify({
      response: generateFallback(error.message),
      metadata: {
        tier: 'FALLBACK',
        error: error.message,
      },
    }), {
      status: 200, // Return 200 with fallback, not 500
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}

function generateFallback(errorMsg) {
  return `I'm having trouble connecting to my analysis engine right now. 

**What I can tell you:**
• Multi-Family: ~10-20 units/acre typical for R-2/R-3 zoning
• Self-Storage: 40-50% lot coverage, $1.25-2.00/SF/month rents
• Industrial: 55% lot coverage typical, 32' clear height standard
• Senior Living: 25 beds/acre, $4,500/month average rate

Please try again in a moment, or switch to Form Mode for calculations.

_Error: ${errorMsg}_`;
}

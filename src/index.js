#!/usr/bin/env node
/**
 * SPD Ordinance Scraper - Main Entry Point
 * Orchestrates scraping and storage pipeline
 */

const MunicodeScraper = require('./scrapers/municode_scraper');
const OrdinanceStorage = require('./storage/supabase_client');

// Configuration
const CONFIG = {
  supabaseUrl: process.env.SUPABASE_URL || 'https://mocerqjnksmhcjzxrewo.supabase.co',
  supabaseKey: process.env.SUPABASE_KEY,
  headless: process.env.HEADLESS !== 'false'
};

/**
 * Scrape a municipality and store results
 */
async function scrapeMunicipality(state, municipality, options = {}) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🏛️ SPD Ordinance Scraper`);
  console.log(`📍 ${municipality}, ${state}`);
  console.log(`${'='.repeat(60)}\n`);

  const scraper = new MunicodeScraper({
    headless: options.headless ?? CONFIG.headless,
    timeout: options.timeout || 60000
  });

  // Scrape municipality
  const results = await scraper.scrapeFullMunicipality(state, municipality);

  // Store in Supabase if key provided
  if (CONFIG.supabaseKey) {
    console.log('\n💾 Storing results in Supabase...');
    const storage = new OrdinanceStorage(CONFIG.supabaseUrl, CONFIG.supabaseKey);
    
    try {
      // Store raw results
      await storage.storeRawResults(results);
      
      // Store structured data
      if (results.status === 'success') {
        const muniId = await storage.storeMunicipalityData(results);
        console.log(`✅ Stored with municipality ID: ${muniId}`);
      }
    } catch (err) {
      console.error(`❌ Storage error: ${err.message}`);
    }
  } else {
    console.log('\n⚠️ SUPABASE_KEY not set - skipping storage');
  }

  // Output results
  console.log('\n📊 Results Summary:');
  console.log(`   Status: ${results.status}`);
  if (results.status === 'success') {
    console.log(`   TOC Sections: ${results.toc?.sections?.length || 0}`);
    console.log(`   Zoning Districts: ${results.zoningDistricts?.districts?.length || 0}`);
    console.log(`   Site Plan Sections: ${results.sitePlanReview?.sections?.length || 0}`);
  } else {
    console.log(`   Error: ${results.error}`);
  }

  return results;
}

/**
 * Batch scrape multiple municipalities
 */
async function batchScrape(municipalities) {
  const results = [];
  
  for (const { state, municipality } of municipalities) {
    try {
      const result = await scrapeMunicipality(state, municipality);
      results.push(result);
      
      // Rate limiting - wait 5 seconds between scrapes
      await new Promise(resolve => setTimeout(resolve, 5000));
    } catch (err) {
      results.push({
        municipality,
        state,
        status: 'error',
        error: err.message
      });
    }
  }

  return results;
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.log('SPD Ordinance Scraper');
    console.log('');
    console.log('Usage:');
    console.log('  node index.js <state> <municipality>');
    console.log('  node index.js --batch <config.json>');
    console.log('');
    console.log('Examples:');
    console.log('  node index.js FL Malabar');
    console.log('  node index.js FL "Palm Bay"');
    console.log('');
    console.log('Environment Variables:');
    console.log('  SUPABASE_URL - Supabase project URL');
    console.log('  SUPABASE_KEY - Supabase anon/service key');
    console.log('  HEADLESS     - Set to "false" for visible browser');
    process.exit(1);
  }

  if (args[0] === '--batch') {
    const config = require(args[1]);
    batchScrape(config.municipalities)
      .then(results => {
        console.log('\n📈 Batch Complete:');
        console.log(`   Success: ${results.filter(r => r.status === 'success').length}`);
        console.log(`   Failed: ${results.filter(r => r.status === 'error').length}`);
      })
      .catch(err => {
        console.error(err);
        process.exit(1);
      });
  } else {
    const [state, ...muniParts] = args;
    const municipality = muniParts.join(' ');
    
    scrapeMunicipality(state, municipality)
      .then(results => {
        // Write to file
        const fs = require('fs');
        const filename = `${municipality.toLowerCase().replace(/\s+/g, '_')}_${state.toLowerCase()}_results.json`;
        fs.writeFileSync(filename, JSON.stringify(results, null, 2));
        console.log(`\n📁 Results saved to: ${filename}`);
      })
      .catch(err => {
        console.error(err);
        process.exit(1);
      });
  }
}

module.exports = { scrapeMunicipality, batchScrape };

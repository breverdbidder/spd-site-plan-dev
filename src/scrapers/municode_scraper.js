/**
 * Municode Ordinance Scraper
 * SPD Site Plan Development - Ordinance Intelligence Module
 * 
 * Uses Puppeteer to scrape municipal codes from Municode Library
 * Handles anti-bot protection that blocks direct HTTP requests
 */

const puppeteer = require('puppeteer');

class MunicodeScraper {
  constructor(options = {}) {
    this.baseUrl = 'https://library.municode.com';
    this.timeout = options.timeout || 60000;
    this.headless = options.headless !== false;
    this.browser = null;
    this.page = null;
  }

  async init() {
    this.browser = await puppeteer.launch({
      headless: this.headless ? 'new' : false,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu'
      ]
    });
    this.page = await this.browser.newPage();
    await this.page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );
    await this.page.setViewport({ width: 1280, height: 800 });
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  /**
   * Build Municode URL for a municipality
   */
  buildUrl(state, municipality, nodeId = null) {
    const stateCode = state.toLowerCase();
    const muni = municipality.toLowerCase().replace(/\s+/g, '_');
    let url = `${this.baseUrl}/${stateCode}/${muni}/codes/code_of_ordinances`;
    if (nodeId) {
      url += `?nodeId=${nodeId}`;
    }
    return url;
  }

  /**
   * Scrape the main table of contents
   */
  async scrapeTOC(state, municipality) {
    const url = this.buildUrl(state, municipality);
    console.log(`📖 Scraping TOC: ${url}`);
    
    await this.page.goto(url, { waitUntil: 'networkidle2', timeout: this.timeout });
    
    // Wait for content to load
    await this.page.waitForSelector('a[href*="nodeId"]', { timeout: 30000 });
    
    const toc = await this.page.evaluate(() => {
      const sections = [];
      document.querySelectorAll('a[href*="nodeId"]').forEach(link => {
        const text = link.textContent.trim();
        const href = link.href;
        const nodeId = new URL(href).searchParams.get('nodeId');
        if (text && nodeId && text.length > 3) {
          sections.push({
            title: text.substring(0, 200),
            nodeId: nodeId,
            url: href
          });
        }
      });
      return sections;
    });

    return {
      municipality,
      state,
      url,
      scrapedAt: new Date().toISOString(),
      sections: toc
    };
  }

  /**
   * Scrape a specific section by nodeId
   */
  async scrapeSection(state, municipality, nodeId) {
    const url = this.buildUrl(state, municipality, nodeId);
    console.log(`📄 Scraping section: ${nodeId}`);
    
    await this.page.goto(url, { waitUntil: 'networkidle2', timeout: this.timeout });
    
    // Wait for content
    await this.page.waitForSelector('body', { timeout: 30000 });
    
    const content = await this.page.evaluate(() => {
      const result = {
        title: document.title,
        text: '',
        subsections: []
      };
      
      // Get main content text
      const mainContent = document.querySelector('.chunk-content, #codebankContent, main, article');
      if (mainContent) {
        result.text = mainContent.innerText.substring(0, 50000);
      }
      
      // Get subsection links
      document.querySelectorAll('a[href*="nodeId"]').forEach(link => {
        const text = link.textContent.trim();
        const href = link.href;
        const nodeId = new URL(href).searchParams.get('nodeId');
        if (text && nodeId && text.length > 3) {
          result.subsections.push({
            title: text.substring(0, 200),
            nodeId: nodeId
          });
        }
      });
      
      return result;
    });

    return {
      nodeId,
      url,
      scrapedAt: new Date().toISOString(),
      ...content
    };
  }

  /**
   * Extract zoning districts from Land Development Code
   */
  async scrapeZoningDistricts(state, municipality) {
    // First get TOC to find zoning section
    const toc = await this.scrapeTOC(state, municipality);
    
    // Look for Land Development Code or Zoning sections
    const zoningKeywords = ['zoning', 'land development', 'land use', 'district'];
    const potentialSections = toc.sections.filter(s => 
      zoningKeywords.some(kw => s.title.toLowerCase().includes(kw))
    );

    const districts = [];
    
    for (const section of potentialSections.slice(0, 5)) {
      const content = await this.scrapeSection(state, municipality, section.nodeId);
      
      // Extract district codes using regex patterns
      const districtPatterns = [
        /([A-Z]{1,3}-\d+[A-Z]*)\s*[-–]\s*([^.\n]+)/g,  // R-1 - Residential
        /([A-Z]{2,4})\s+[-–]\s+([^.\n]+(?:district|zone))/gi,  // RR - Rural Residential
        /(?:district|zone)\s+([A-Z]{1,3}-?\d*[A-Z]*)/gi  // District R-1
      ];

      for (const pattern of districtPatterns) {
        let match;
        while ((match = pattern.exec(content.text)) !== null) {
          const code = match[1].toUpperCase();
          const name = match[2] ? match[2].trim() : '';
          if (code.length >= 2 && !districts.find(d => d.code === code)) {
            districts.push({ code, name, sourceSection: section.title });
          }
        }
      }
    }

    return {
      municipality,
      state,
      scrapedAt: new Date().toISOString(),
      districts,
      sourceSections: potentialSections.map(s => s.title)
    };
  }

  /**
   * Scrape site plan review requirements
   */
  async scrapeSitePlanRequirements(state, municipality) {
    const toc = await this.scrapeTOC(state, municipality);
    
    // Find site plan sections
    const sitePlanSections = toc.sections.filter(s => 
      s.title.toLowerCase().includes('site plan') ||
      s.title.toLowerCase().includes('site development')
    );

    const requirements = {
      municipality,
      state,
      scrapedAt: new Date().toISOString(),
      sections: [],
      applicabilityTriggers: [],
      reviewProcess: [],
      requiredDocuments: []
    };

    for (const section of sitePlanSections.slice(0, 3)) {
      const content = await this.scrapeSection(state, municipality, section.nodeId);
      requirements.sections.push({
        title: section.title,
        nodeId: section.nodeId,
        textSample: content.text.substring(0, 2000)
      });

      // Extract applicability triggers
      const triggerPatterns = [
        /shall be required for[:\s]+([^.]+)/gi,
        /site plan (?:approval|review) (?:is |shall be )?required[:\s]+([^.]+)/gi,
        /(?:any|all) ([^.]+) shall require site plan/gi
      ];

      for (const pattern of triggerPatterns) {
        let match;
        while ((match = pattern.exec(content.text)) !== null) {
          const trigger = match[1].trim();
          if (trigger.length > 10 && !requirements.applicabilityTriggers.includes(trigger)) {
            requirements.applicabilityTriggers.push(trigger);
          }
        }
      }
    }

    return requirements;
  }

  /**
   * Full municipality scrape - zoning + site plan + TOC
   */
  async scrapeFullMunicipality(state, municipality) {
    console.log(`🏛️ Starting full scrape: ${municipality}, ${state}`);
    
    await this.init();
    
    try {
      const results = {
        municipality,
        state,
        scrapedAt: new Date().toISOString(),
        scraperVersion: '1.0.0',
        status: 'success',
        toc: null,
        zoningDistricts: null,
        sitePlanReview: null
      };

      // Get TOC
      results.toc = await this.scrapeTOC(state, municipality);
      console.log(`📑 Found ${results.toc.sections.length} TOC sections`);

      // Get zoning districts
      results.zoningDistricts = await this.scrapeZoningDistricts(state, municipality);
      console.log(`🏘️ Found ${results.zoningDistricts.districts.length} zoning districts`);

      // Get site plan requirements
      results.sitePlanReview = await this.scrapeSitePlanRequirements(state, municipality);
      console.log(`📋 Found ${results.sitePlanReview.sections.length} site plan sections`);

      return results;

    } catch (error) {
      console.error(`❌ Scrape failed: ${error.message}`);
      return {
        municipality,
        state,
        scrapedAt: new Date().toISOString(),
        status: 'error',
        error: error.message
      };
    } finally {
      await this.close();
    }
  }
}

module.exports = MunicodeScraper;

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.log('Usage: node municode_scraper.js <state> <municipality>');
    console.log('Example: node municode_scraper.js FL Malabar');
    process.exit(1);
  }

  const [state, ...muniParts] = args;
  const municipality = muniParts.join(' ');

  const scraper = new MunicodeScraper();
  scraper.scrapeFullMunicipality(state, municipality)
    .then(results => {
      console.log(JSON.stringify(results, null, 2));
    })
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}

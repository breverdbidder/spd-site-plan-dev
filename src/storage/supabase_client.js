/**
 * Supabase Client for SPD Ordinance Storage
 * Stores scraped municipal ordinance data
 */

const { createClient } = require('@supabase/supabase-js');

class OrdinanceStorage {
  constructor(supabaseUrl, supabaseKey) {
    this.supabase = createClient(supabaseUrl, supabaseKey);
  }

  /**
   * Store municipality ordinance data
   */
  async storeMunicipalityData(data) {
    const { municipality, state, scrapedAt, status } = data;
    
    // Upsert municipality record
    const { data: muniRecord, error: muniError } = await this.supabase
      .from('municipalities')
      .upsert({
        name: municipality,
        state: state,
        last_scraped: scrapedAt,
        scrape_status: status,
        municode_url: data.toc?.url || null
      }, {
        onConflict: 'name,state'
      })
      .select()
      .single();

    if (muniError) throw muniError;
    
    const municipalityId = muniRecord.id;

    // Store zoning districts
    if (data.zoningDistricts?.districts) {
      for (const district of data.zoningDistricts.districts) {
        await this.supabase
          .from('zoning_districts')
          .upsert({
            municipality_id: municipalityId,
            code: district.code,
            name: district.name,
            source_section: district.sourceSection,
            updated_at: scrapedAt
          }, {
            onConflict: 'municipality_id,code'
          });
      }
    }

    // Store site plan requirements
    if (data.sitePlanReview?.sections) {
      for (const section of data.sitePlanReview.sections) {
        await this.supabase
          .from('ordinance_sections')
          .upsert({
            municipality_id: municipalityId,
            section_type: 'site_plan_review',
            title: section.title,
            node_id: section.nodeId,
            content_sample: section.textSample,
            updated_at: scrapedAt
          }, {
            onConflict: 'municipality_id,node_id'
          });
      }
    }

    // Store TOC sections
    if (data.toc?.sections) {
      for (const section of data.toc.sections.slice(0, 100)) {
        await this.supabase
          .from('ordinance_sections')
          .upsert({
            municipality_id: municipalityId,
            section_type: 'toc',
            title: section.title,
            node_id: section.nodeId,
            municode_url: section.url,
            updated_at: scrapedAt
          }, {
            onConflict: 'municipality_id,node_id'
          });
      }
    }

    return municipalityId;
  }

  /**
   * Store raw scrape results
   */
  async storeRawResults(data) {
    const { error } = await this.supabase
      .from('scrape_results')
      .insert({
        municipality: data.municipality,
        state: data.state,
        scraped_at: data.scrapedAt,
        status: data.status,
        raw_data: data,
        error_message: data.error || null
      });

    if (error) throw error;
  }

  /**
   * Get zoning districts for a municipality
   */
  async getZoningDistricts(municipality, state) {
    const { data, error } = await this.supabase
      .from('zoning_districts')
      .select(`
        code,
        name,
        source_section,
        municipalities!inner(name, state)
      `)
      .eq('municipalities.name', municipality)
      .eq('municipalities.state', state);

    if (error) throw error;
    return data;
  }

  /**
   * Get site plan sections for a municipality
   */
  async getSitePlanSections(municipality, state) {
    const { data, error } = await this.supabase
      .from('ordinance_sections')
      .select(`
        title,
        node_id,
        content_sample,
        municode_url,
        municipalities!inner(name, state)
      `)
      .eq('municipalities.name', municipality)
      .eq('municipalities.state', state)
      .eq('section_type', 'site_plan_review');

    if (error) throw error;
    return data;
  }
}

module.exports = OrdinanceStorage;

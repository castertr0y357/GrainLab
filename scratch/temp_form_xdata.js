const xData = {
          texture: 0,
          crumb: 0,
          starter: 0,
          leaven: 'yeast',
          get leavening_type() { return this.leaven; },
          grain: '',
          maturity: '',
          portioned: false,
          subOriginal: 'water',
          subSubstitute: 'none',
          use_custom: false,
          category_slug: '',
          custom_mixer: 'static',
          mixing_method: 'stand_mixer',
          secondary_lipid: 'unsalted_butter',
          secondary_liquid: 'pure_water',
          secondary_binder: 'none',
          proofing_environment: 'ambient',
          mill_type: 'stoneground',
          form_factor_val: '',
          recommended_ff_slug: '',
          yield_scale: 1.0,
          fat_starting_temp: 'room_temp',
          workspace_temp: 65,
          liquid_temp: 40,
          active_action: 'knead',
          hardware_registry: [
              { id: 'stand_mixer', name: 'Stand Mixer', category: 'high_torque' },
              { id: 'bread_machine', name: 'Bread Machine', category: 'high_torque' },
              { id: 'food_processor', name: 'Food Processor', category: 'high_torque' },
              { id: 'hand_beaters', name: 'Hand Beaters', category: 'whipping_whisk' },
              { id: 'whisk', name: 'Hand Whisk', category: 'whipping_whisk' },
              { id: 'spatula_bowl', name: 'Manual Spatula & Bowl', category: 'zero_friction' }
          ],
          get activeProductionProfile() {
              return this.engines_ff[this.selected_master]?.production_profile || {
                  thermodynamic_focus: 'biological_yeast_activity',
                  mechanical_energy_threshold: 'high_kneading',
                  permissible_action_types: ['knead'],
                  environmental_rest_strategy: 'gas_proofing'
              };
          },
          get filteredTools() {
              const threshold = this.activeProductionProfile.mechanical_energy_threshold;
              if (threshold === 'high_kneading' || threshold === 'moderate_shearing' || threshold === 'mechanical_compaction') {
                  return this.hardware_registry.filter(t => t.category === 'high_torque' || t.category === 'zero_friction');
              } else if (threshold === 'low_emulsifying') {
                  return this.hardware_registry.filter(t => t.category === 'whipping_whisk' || t.category === 'zero_friction');
              } else if (threshold === 'minimal_folding') {
                  return this.hardware_registry.filter(t => t.category === 'zero_friction');
              }
              return this.hardware_registry;
          },
          engines_ff: JSON.parse(''),
          enginesArchetypes: JSON.parse(''),
          get formFactorBaseline() {
              const activeEngineFFs = this.engines_ff[this.selected_master]?.permissible_form_factors || {};
              return activeEngineFFs[this.form_factor_val] || { 
                  name: 'Standard Loaf',
                  is_portioned: false, 
                  unit_weight: 900, 
                  base_count: 1, 
                  step_increment: 1,
                  unit_label: 'loaf', 
                  unit_label_plural: 'loaves',
                  bake_temp_f: 375,
                  bake_time_min: 45,
                  steam_required: false,
                  is_enriched_profile: false
              };
          },
          get yieldHelperString() {
              const ff = this.formFactorBaseline;
              const totalCount = Math.round(ff.base_count * this.yield_scale);
              const label = totalCount === 1 ? ff.unit_label : ff.unit_label_plural;
              if (ff.is_portioned) {
                  return `Yield Matrix: Generates ${totalCount} total ${label} (Portion cleanly into uniform ~${Math.round(ff.unit_weight)}g pieces before proofing)`;
              } else {
                  const totalWeight = Math.round(ff.unit_weight * ff.base_count * this.yield_scale);
                  const displayCount = (ff.base_count * this.yield_scale);
                  const displayLabel = displayCount === 1 ? ff.unit_label : ff.unit_label_plural;
                  return `Yield Matrix: Generates ${displayCount} total ${displayLabel} (Total dough weight: ~${totalWeight}g)`;
              }
          },
          getFormFactorButtonStyle(ff_slug, ff_data) {
              if (this.form_factor_val === ff_slug) {
                  if (this.geometry_status === 'sub-optimal') {
                      return 'background-color: var(--warning); color: #000; border-color: var(--warning); box-shadow: 0 0 15px var(--warning); font-weight: 800;';
                  } else {
                      return 'background-color: var(--accent); color: #000; border-color: var(--accent); box-shadow: 0 0 15px var(--accent); font-weight: 800;';
                  }
              } else {
                  return 'background: transparent; color: var(--text-primary);';
              }
          },
          sortedBerriesFor(berries) {
              const evs = grainEvaluations || [];
              if (!evs || evs.length === 0) return berries || [];
              const score = { 'recommended': 1, 'sub-optimal': 2, 'indifferent': 3, 'not-recommended': 4 };
              return [...(berries || [])].sort((a, b) => {
                  const eA = evs.find(e => e.grain_id === a.id);
                  const eB = evs.find(e => e.grain_id === b.id);
                  const sA = score[eA ? eA.tier : 'indifferent'] || 3;
                  const sB = score[eB ? eB.tier : 'indifferent'] || 3;
                  if (sA !== sB) return sA - sB;
                  return a.name.localeCompare(b.name);
              });
          },
          getGrainStyle(berry) {
              const evs = grainEvaluations || [];
              if (evs && evs.length > 0) {
                  const ev = evs.find(e => e.grain_id === berry.id);
                  if (ev) {
                      if (ev.tier === 'recommended') {
                          return berry.selected
                              ? 'border-color: #ffd700; box-shadow: 0 0 12px rgba(255,215,0,0.6); background-color: rgba(255,215,0,0.08);'
                              : 'border-color: #ffd700; box-shadow: 0 0 8px rgba(255,215,0,0.3); background-color: rgba(255,215,0,0.02);';
                      } else if (ev.tier === 'sub-optimal') {
                          return berry.selected
                              ? 'border-color: var(--warning); box-shadow: 0 0 12px rgba(255,193,7,0.6); background-color: rgba(255,193,7,0.08);'
                              : 'border-color: var(--warning); box-shadow: 0 0 8px rgba(255,193,7,0.3); background-color: rgba(255,193,7,0.02);';
                      } else if (ev.tier === 'not-recommended') {
                          return berry.selected
                              ? 'border-color: var(--danger); box-shadow: 0 0 12px rgba(220,53,69,0.6); background-color: rgba(220,53,69,0.08);'
                              : 'border-color: var(--danger); box-shadow: 0 0 8px rgba(220,53,69,0.3); background-color: rgba(220,53,69,0.02);';
                      }
                  }
              }
              return berry.selected
                  ? 'border-color: var(--accent); background-color: rgba(255,136,0,0.05);'
                  : '';
          }
      };
module.exports = xData;
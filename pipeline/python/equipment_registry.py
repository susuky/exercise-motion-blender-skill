"""Independent equipment taxonomy; no upstream proprietary media used."""
EQUIPMENT_TAXONOMY = {
 'rigid_bilateral_bar': ('barbell','olympic_barbell','ez_barbell','trap_bar','smith_machine','stick','hammer','wheel_roller'),
 'independent_handheld': ('dumbbell','kettlebell','medicine_ball','weighted'),
 'wave_rope': ('battle_ropes','rope'),
 'elastic_tether': ('band','resistance_band','suspension'),
 'cable_pulley_station': ('cable','cable_machine'),
 'pivoting_lever_station': ('leverage_machine','lever_machine','assisted'),
 'linear_sled_carriage': ('power_sled','sled_machine','pilates_machine'),
 'floor_prop_surface': ('body_weight','bodyweight','bench','bosu_ball','stability_ball','roll','rollball','vibrate_plate'),
}
ALIASES = {'body weight':'body_weight','battle rope':'battle_ropes','battling rope':'battle_ropes','smith machine':'smith_machine','ez barbell':'ez_barbell','olympic barbell':'olympic_barbell','leverage machine':'leverage_machine','resistance band':'resistance_band','kettlebells':'kettlebell','dumbbells':'dumbbell'}
def normalize_equipment_type(kind):
    key = str(kind).strip().lower().replace('-', '_').replace(' ', '_')
    return ALIASES.get(key, key)
def get_equipment_archetype(kind):
    normalized = normalize_equipment_type(kind)
    for family, types in EQUIPMENT_TAXONOMY.items():
        if normalized in types:
            return family
    return 'unknown'

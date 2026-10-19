/* Cheap first print: full circumference ring + separate closed-loop gauge.
   Module imports use the original source's lexical fit parameters.
   Override values with -D, or change defaults in the main source.
   Coupon is printed flat WITHOUT the rear acoustic window; no supports.
   The continuous rear lip is a conservative retention check.
   Install/removal test must use the SAME filament, scale and layer height. */

// OpenSCAD imports module definitions with their original lexical globals.
use <moto_tag_collar_holder.scad>

// Additional coupon settings independent of the main output transform.
coupon_gap = 4;
coupon_outer_r = holder_outer_radius();
coupon_slot_h = loop_profile_height();

ring_only(false);
translate([coupon_outer_r + coupon_gap + coupon_slot_h/2,0,0])
    rotate([0,0,90]) closed_loop_local();

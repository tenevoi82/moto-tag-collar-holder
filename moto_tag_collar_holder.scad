/* Moto Tag gen.1 / leather collar, TPU 95A. Units: mm.
   Default export is tilted 45 degrees for printing WITH local supports.
   Set print_orientation=false for assembled coordinates (collar travels X).
   Rounded tag edge is an assumption, not a measured Motorola CAD profile.
   See README.md and fit_test.scad before use. OpenSCAD 2021.01 compatible. */

/* [Measured dimensions] */
tag_diameter = 31.9;
tag_thickness = 8.0;
collar_width = 21.5;
collar_thickness = 3.85;

/* [Fit adjustments] */
collar_width_clearance = 0.8;      // TOTAL width clearance, not per side
collar_thickness_clearance = 0.6;  // TOTAL thickness clearance
tag_radial_clearance = 0.2;       // PER SIDE at maximum tag diameter
tag_axial_clearance = 0.4;        // TOTAL between nominal front/rear seats
tag_edge_radius_assumed = 0.8;    // measure/test; rounded disc approximation
retention_lip = 0.6;             // inward overlap from assumed rounded FACE
retention_lip_height = 0.9;       // each seat's extra axial allowance

/* [Structure] */
ring_wall_thickness = 2.0;
edge_radius = 1.0;               // external ring/loop profile corner radius
loop_wall = 2.0;
loop_length = 3.2;               // each closed belt loop's length along X
slot_corner_radius = 0.6;
loop_entry_bevel = 0.35;
grip_rib_height = 0.25;           // each side; minimum free gap = slot_t-2*this
vent_gap = 1.2;                  // minimum rear air gap AFTER design belt bend
collar_bend_radius = 40;         // minimum design OUTSIDE bend radius of collar
loop_inset = 5.65;               // loop centre inboard of outer ring radius
arm_width = 4.0;
arm_height = 2.4;
speaker_angle = 90;              // +Y; rotate tag buzzer into this sector
speaker_angle_width = 50;
speaker_window_height = 2.4;

/* [Output] */
print_orientation = true;
show_reference = false;         // translucent references: preview only
quality = 192;                  // circumference facets

/* [Hidden] */
$fn = quality;
eps = 0.02;
bore_r = tag_diameter/2 + tag_radial_clearance;
outer_r = bore_r + ring_wall_thickness;
throat_r = bore_r - tag_edge_radius_assumed - retention_lip;
mouth_bevel = 0.25;
transition_height = mouth_bevel + bore_r - throat_r; // 45 degree ramp
ring_height = tag_thickness + tag_axial_clearance + 2*retention_lip_height;
slot_w = collar_width + collar_width_clearance;
slot_t = collar_thickness + collar_thickness_clearance;
loop_outer_w = slot_w + 2*loop_wall;
loop_outer_h = slot_t + 2*loop_wall;
loop_x = outer_r - loop_inset;
curve_half_span = loop_x + loop_length/2;
curvature_sag = collar_bend_radius -
    sqrt(pow(collar_bend_radius,2)-pow(curve_half_span,2));
// Keep rear face above a curved belt; also keep it >=0.5 above loop roofs.
ring_base = max(loop_wall+slot_t+vent_gap+curvature_sag-
                retention_lip_height-tag_axial_clearance/2,
                loop_outer_h+0.5-retention_lip_height-tag_axial_clearance/2);
arm_y = slot_w/2 + loop_wall/2;
arm_root_x = sqrt(pow(outer_r-0.8,2)-pow(arm_y,2));
tag_back = ring_base + retention_lip_height + tag_axial_clearance/2;
// Analytic lowest point of rounded loop profile after X rotation by 45 deg.
print_lift = (loop_outer_w/2 - edge_radius*(2-sqrt(2)))/sqrt(2);

assert(tag_edge_radius_assumed >= 0 && tag_edge_radius_assumed < tag_thickness/2);
assert(tag_radial_clearance >= 0 && retention_lip > tag_radial_clearance);
assert(throat_r > 0 && ring_height > 2*transition_height + 1);
assert(ring_wall_thickness >= 1.6 && loop_wall >= 1.6 && arm_width >= 3.2);
assert(loop_length > 2*loop_entry_bevel + 1);
assert(grip_rib_height >= 0 && grip_rib_height < loop_wall/2);
assert(edge_radius > 0 && edge_radius <= loop_wall/2);
assert(slot_corner_radius < min(slot_w,slot_t)/2);
assert(arm_y < outer_r-0.8, "Collar too wide for this compact two-loop design");
assert(collar_bend_radius > curve_half_span+5);
assert(loop_x-loop_length/2 > 5 && loop_x < outer_r);
assert(vent_gap >= 1.0);
assert(speaker_window_height < ring_height/2);
assert(speaker_angle == 90 || speaker_angle == 270,
       "Use lateral speaker sectors, clear of the loop connections");

module rounded_rect_2d(w,h,r) {
    offset(r=r) square([w-2*r,h-2*r],center=true);
}

module ring_outer() {
    rr = min(edge_radius,ring_wall_thickness/2);
    rotate_extrude(convexity=10)
        polygon(concat([[0,0],[outer_r-rr,0]],
            [for(a=[-90:5:0]) [outer_r-rr+rr*cos(a),rr+rr*sin(a)]],
            [[outer_r,ring_height-rr]],
            [for(a=[0:5:90])
                [outer_r-rr+rr*cos(a),ring_height-rr+rr*sin(a)]],
            [[0,ring_height]]));
}

// Continuous front and rear lips; no thin cantilever snap fingers.
module tag_void() {
    rotate_extrude(convexity=10) polygon([
        [0,-eps],[throat_r+mouth_bevel,-eps],
        [throat_r+mouth_bevel,0],[throat_r,mouth_bevel],
        [bore_r,transition_height],
        [bore_r,ring_height-transition_height],
        [throat_r,ring_height-mouth_bevel],
        [throat_r+mouth_bevel,ring_height],
        [throat_r+mouth_bevel,ring_height+eps],[0,ring_height+eps]]);
}

module speaker_cut() {
    translate([0,0,-eps]) linear_extrude(speaker_window_height+eps)
        polygon(concat([[0,0]], [for(a=[speaker_angle-speaker_angle_width/2:
            1:speaker_angle+speaker_angle_width/2])
            [(outer_r+3)*cos(a),(outer_r+3)*sin(a)]]));
}

module ring_only(acoustic_window=true) {
    difference() {
        ring_outer();
        tag_void();
        if(acoustic_window) speaker_cut();
    }
}

// Local coordinates: profile XY maps to installed YZ, extrusion Z to X.
module closed_loop_local() {
    $fn = 64;
    b = loop_entry_bevel;
    union() {
    difference() {
        hull() {
            for(z=[b,loop_length-b-eps]) translate([0,0,z])
                linear_extrude(eps)
                    rounded_rect_2d(loop_outer_w,loop_outer_h,edge_radius);
            for(z=[0,loop_length-eps]) translate([0,0,z])
                linear_extrude(eps)
                    rounded_rect_2d(loop_outer_w-2*b,loop_outer_h-2*b,
                                    edge_radius-b);
        }
        translate([0,0,-eps]) linear_extrude(loop_length+2*eps)
            rounded_rect_2d(slot_w,slot_t,slot_corner_radius);
        // Entry bevel on both mouths, leaving a full-size central gauge land.
        for(mirror_end=[false,true])
            translate([0,0,mirror_end ? loop_length : 0])
                scale([1,1,mirror_end ? -1 : 1]) hull() {
                    translate([0,0,-eps]) linear_extrude(eps)
                        rounded_rect_2d(slot_w+2*b,slot_t+2*b,slot_corner_radius+b);
                    translate([0,0,b]) linear_extrude(eps)
                        rounded_rect_2d(slot_w,slot_t,slot_corner_radius);
                }
    }
    // Broad round TPU ridges, not teeth. The coupon shares these ridges.
    r = 0.8;
    if(grip_rib_height > 0)
        for(v=[-slot_t/2+grip_rib_height-r,
               slot_t/2-grip_rib_height+r])
            hull() for(u=[-slot_w/2+1.5,slot_w/2-1.5])
                translate([u,v,loop_length/2]) sphere(r=r,$fn=32);
    }
}

function holder_outer_radius() = outer_r;
function loop_profile_height() = loop_outer_h;
// Shared assembly dimensions for optional collar-captured protective grille.
// Pure accessor: the original holder and fit-test geometry are unchanged.
function holder_geometry() = [outer_r,ring_base,ring_height,
    tag_back+tag_thickness,loop_outer_h,loop_x,loop_length,arm_y,print_lift];

module belt_loop(s=1) {
    translate([s*loop_x-loop_length/2,0,loop_outer_h/2])
        multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
            closed_loop_local();
}

module bridge_arm(sx,sy) {
    $fn = 48;
    // Four rounded risers; 1.2 mm embed into loop side wall / roof.
    arm_z = loop_outer_h-1.2;
    arm_h = ring_base+arm_height-arm_z;
    translate([0,0,arm_z]) hull() {
        for(x=[sx*arm_root_x,sx*loop_x])
            translate([x,sy*arm_y,0]) {
                for(z=[0.35,arm_h-0.35-eps])
                    translate([0,0,z]) cylinder(r=arm_width/2,h=eps);
                for(z=[0,arm_h-eps])
                    translate([0,0,z]) cylinder(r=arm_width/2-0.35,h=eps);
            }
    }
}

module holder_installed() {
    difference() {
        union() {
            translate([0,0,ring_base]) ring_outer();
            for(s=[-1,1]) belt_loop(s);
            for(sx=[-1,1],sy=[-1,1]) bridge_arm(sx,sy);
        }
        // Cut AFTER union: web roots must never intrude into tag cavity.
        translate([0,0,ring_base]) {
            tag_void();
            speaker_cut();
        }
    }
}

module tag_reference() {
    e = tag_edge_radius_assumed;
    translate([0,0,tag_back])
        if(e>0) rotate_extrude() polygon(concat(
            [[0,0],[tag_diameter/2-e,0]],
            [for(a=[-90:5:0]) [tag_diameter/2-e+e*cos(a),e+e*sin(a)]],
            [[tag_diameter/2,tag_thickness-e]],
            [for(a=[0:5:90])
                [tag_diameter/2-e+e*cos(a),tag_thickness-e+e*sin(a)]],
            [[0,tag_thickness]]));
        else cylinder(d=tag_diameter,h=tag_thickness);
}

module references() {
    %color([0.2,0.6,0.9,0.45]) tag_reference();
    %color([0.45,0.22,0.1,0.45])
        translate([-34,-collar_width/2,loop_wall+collar_thickness_clearance/2])
            cube([68,collar_width,collar_thickness]);
}

module output_model() {
    holder_installed();
    if(show_reference && $preview) references();
}

if(print_orientation)
    translate([0,0,print_lift]) rotate([45,0,0]) output_model();
else output_model();

echo(bore_diameter=2*bore_r, lip_throat_diameter=2*throat_r,
     collar_slot=[slot_w,slot_t], ring_height=ring_height,
     installed_height=ring_base+ring_height,
     rear_air_gap_min=tag_back-(loop_wall+slot_t),
     curve_sag=curvature_sag, minimum_curved_air_gap=tag_back-
        (loop_wall+slot_t+curvature_sag),
     nominal_equator_stretch_percent=100*(tag_diameter/(2*throat_r)-1));

/* Moto Tag protective grille: separate TPU 95A cap captured by the SAME
   collar as the proven base holder. Units mm. No latch, glue or metal parts.
   Insert tag into the original holder, place cap over it, then thread collar
   through all FOUR closed loops. Remove collar to service the battery.
   Not waterproof, not load-rated, no claim of absolute retention. */
use <moto_tag_collar_holder.scad>

/* [Protective grille] */
grid_pitch = 7.0;
grid_bar_width = 2.6;
grid_thickness = 2.4;
grid_hole_radius = 0.65;
button_face_gap = 2.5; // to assumed nominal tag front; actual button to be checked
cap_radial_clearance = 0.35; // per side, over original ring OD
cap_wall = 2.2;
cap_skirt_overlap = 4.5;
cap_loop_x = 20.7; // loops pass OUTSIDE body OD during straight cap installation
cap_post_width = 4.0;

/* [Output] */
output_part = "plate"; // [plate,cap,cap_installed,assembly]
plate_half_spacing = 30;
quality = 96;

/* [Hidden] */
$fn=quality;
eps=0.02;
g=holder_geometry();
body_r=g[0]; body_base=g[1]; body_ring_height=g[2];
tag_front=g[3]; loop_h=g[4]; body_loop_x=g[5];
loop_length=g[6]; loop_arm_y=g[7]; body_print_lift=g[8];
body_top=body_base+body_ring_height;
cap_inner_r=body_r+cap_radial_clearance;
cap_outer_r=cap_inner_r+cap_wall;
grid_bottom=tag_front+button_face_gap;
cap_top=grid_bottom+grid_thickness;
skirt_bottom=body_top-cap_skirt_overlap;
grid_hole=grid_pitch-grid_bar_width;
grid_count=ceil(cap_inner_r/grid_pitch)+1;
cap_post_root_r=cap_outer_r-0.3;
cap_post_root_x=sqrt(cap_post_root_r*cap_post_root_r-loop_arm_y*loop_arm_y);

assert(grid_bar_width>=2.4 && grid_thickness>=2.0);
assert(grid_hole>2 && grid_hole<6);
assert(grid_hole_radius>0 && grid_hole_radius<grid_hole/2);
assert(button_face_gap>=2.0);
assert(cap_radial_clearance>=0.25 && cap_wall>=2.0);
assert(cap_skirt_overlap>=3.0 && skirt_bottom>loop_h+2.4);
assert(cap_loop_x-loop_length/2 > body_loop_x+loop_length/2+0.8);
assert(cap_loop_x-loop_length/2 > body_r+0.6);
assert(cap_post_root_r-cap_post_width/2 > body_r+0.15);
assert(cap_post_root_r-cap_post_width/2 < cap_outer_r-0.8);

function grille_geometry() = [cap_inner_r,cap_outer_r,grid_bottom,cap_top,
    skirt_bottom,grid_hole,grid_pitch,grid_bar_width,button_face_gap,cap_loop_x];

module grille_face_2d() {
    difference() {
        circle(r=cap_outer_r);
        intersection() {
            circle(r=cap_inner_r);
            union() for(ix=[-grid_count:grid_count],iy=[-grid_count:grid_count])
                translate([ix*grid_pitch,iy*grid_pitch])
                    offset(r=grid_hole_radius)
                        square([grid_hole-2*grid_hole_radius,
                                grid_hole-2*grid_hole_radius],center=true);
        }
    }
}

module grille_face() {
    translate([0,0,grid_bottom])
        linear_extrude(grid_thickness) grille_face_2d();
}

module cap_skirt() {
    // Cylindrical skirt surrounds the existing body with radial clearance.
    // Tiny side drain notches avoid a sealed pocket and are below the grille.
    difference() {
        translate([0,0,skirt_bottom])
            cylinder(r=cap_outer_r,h=grid_bottom+0.4-skirt_bottom);
        translate([0,0,skirt_bottom-eps])
            cylinder(r=cap_inner_r,h=grid_bottom+0.4-skirt_bottom+2*eps);
        for(a=[90,270]) rotate([0,0,a])
            translate([cap_inner_r-0.1,-1.0,skirt_bottom-eps])
                cube([cap_wall+0.3,2.0,1.2+eps]);
    }
}

module cap_loop(s) {
    translate([s*cap_loop_x-loop_length/2,0,loop_h/2])
        multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
            closed_loop_local();
}

module cap_post(sx,sy) {
    // Four sloping braces outside the body OD; overlap loop roofs by 1.2 mm.
    z0=loop_h-1.2;
    z1=skirt_bottom+2.0;
    hull() {
        translate([sx*cap_loop_x,sy*loop_arm_y,z0+0.35])
            cylinder(r=cap_post_width/2,h=eps,$fn=48);
        translate([sx*cap_loop_x,sy*loop_arm_y,z0])
            cylinder(r=cap_post_width/2-0.35,h=eps,$fn=48);
        translate([sx*cap_post_root_x,sy*loop_arm_y,z1-0.35])
            cylinder(r=cap_post_width/2,h=eps,$fn=48);
        translate([sx*cap_post_root_x,sy*loop_arm_y,z1-eps])
            cylinder(r=cap_post_width/2-0.35,h=eps,$fn=48);
    }
}

module grille_cap_installed() {
    union() {
        cap_skirt();
        grille_face();
        for(s=[-1,1]) cap_loop(s);
        for(sx=[-1,1],sy=[-1,1]) cap_post(sx,sy);
    }
}

module grille_cap_print() {
    // Grille face on plate. This keeps support interfaces off the mesh face.
    // The roofs of the remote collar loops still need supports.
    translate([0,0,cap_top]) rotate([180,0,0]) grille_cap_installed();
}

if(output_part=="cap") grille_cap_print();
else if(output_part=="cap_installed") grille_cap_installed();
else if(output_part=="assembly") {
    holder_installed();
    grille_cap_installed();
} else if(output_part=="plate") {
    translate([-plate_half_spacing,0,body_print_lift])
        rotate([45,0,0]) holder_installed();
    translate([plate_half_spacing,0,0]) grille_cap_print();
} else assert(false,"Unknown output_part");

echo(cap_outer_diameter=2*cap_outer_r,grid_cell=grid_hole,
     bar_width=grid_bar_width,grid_thickness=grid_thickness,
     nominal_button_gap=button_face_gap,cap_total_height=cap_top,
     skirt_overlap=cap_skirt_overlap,radial_clearance=cap_radial_clearance,
     cap_loop_spacing=2*cap_loop_x);

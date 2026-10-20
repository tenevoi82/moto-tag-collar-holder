/* Защитная решётка Moto Tag V2 (для корпуса V2): отдельная накладка из TPU 95A.
   Метка вставляется в корпус, накладка надевается сверху, один ремень
   продевается через ВСЕ ЧЕТЫРЕ замкнутых ушка. Для снятия выньте ремень.
   Зазор до метки рассчитан по условному профилю и ещё не подтверждён примеркой.
   Печатный комплект не является герметичным футляром. Размеры в мм. */
use <moto_tag_collar_holder_v2.scad>

/* [Защитная решётка] */
// Шаг ячеек решётки, мм
shag_setki = 7.0;
// Ширина перемычки решётки, мм
shirina_peremychki_setki = 2.6;
// Толщина решётки, мм
tolshchina_setki = 2.4;
// Скругление углов ячейки, мм
skruglenie_yacheyki = 0.65;
// Зазор до условной передней поверхности метки; не измеренный зазор до кнопки, мм
zazor_setki_do_raschetnoy_metki = 2.5;
// Зазор с каждой стороны между юбкой накладки и кольцом, мм
bokovoy_zazor_nakladki = 0.35;
// Толщина стенки юбки накладки, мм
tolshchina_stenki_nakladki = 2.2;
// Перекрытие накладкой верхней части кольца, мм
perehlyost_yubki = 4.5;
// Половина расстояния между центрами ушек накладки, мм
polurasstoyanie_mezhdu_ushkami_nakladki = 20.7;
// Ширина стойки накладки, мм
shirina_stoyki_nakladki = 4.0;

/* [Вид модели] */
// Выбор детали или сборки
vid_modeli = "stol"; // [stol:Корпус и накладка для печати, nakladka:Только накладка для печати, nakladka_v_sborke:Накладка в положении на ошейнике, sborka:Собранный держатель]
// Половина расстояния между деталями на печатном столе, мм
polurasstoyanie_mezhdu_detalyami = 30;
// Количество граней окружности
kachestvo_okruzhnosti = 96;

/* [Hidden] */
$fn=kachestvo_okruzhnosti;
eps=0.02;
g=holder_geometry();
body_r=g[0]; body_base=g[1]; body_ring_height=g[2];
tag_front=g[3]; loop_h=g[4]; body_loop_x=g[5];
// Длина ушка вдоль ремня, мм
dlina_ushka=g[6]; loop_arm_y=g[7]; body_print_lift=g[8];
body_top=body_base+body_ring_height;
cap_inner_r=body_r+bokovoy_zazor_nakladki;
cap_outer_r=cap_inner_r+tolshchina_stenki_nakladki;
grid_bottom=tag_front+zazor_setki_do_raschetnoy_metki;
cap_top=grid_bottom+tolshchina_setki;
skirt_bottom=body_top-perehlyost_yubki;
grid_hole=shag_setki-shirina_peremychki_setki;
grid_count=ceil(cap_inner_r/shag_setki)+1;
cap_post_root_r=cap_outer_r-0.3;
cap_post_root_x=sqrt(cap_post_root_r*cap_post_root_r-loop_arm_y*loop_arm_y);

assert(shirina_peremychki_setki>=2.4 && tolshchina_setki>=2.0);
assert(grid_hole>2 && grid_hole<6);
assert(skruglenie_yacheyki>0 && skruglenie_yacheyki<grid_hole/2);
assert(zazor_setki_do_raschetnoy_metki>=2.0);
assert(bokovoy_zazor_nakladki>=0.25 && tolshchina_stenki_nakladki>=2.0);
assert(perehlyost_yubki>=3.0 && skirt_bottom>loop_h+2.4);
assert(polurasstoyanie_mezhdu_ushkami_nakladki-dlina_ushka/2 > body_loop_x+dlina_ushka/2+0.8);
assert(polurasstoyanie_mezhdu_ushkami_nakladki-dlina_ushka/2 > body_r+0.6);
assert(cap_post_root_r-shirina_stoyki_nakladki/2 > body_r+0.15);
assert(cap_post_root_r-shirina_stoyki_nakladki/2 < cap_outer_r-0.8);

function grille_geometry() = [cap_inner_r,cap_outer_r,grid_bottom,cap_top,
    skirt_bottom,grid_hole,shag_setki,shirina_peremychki_setki,zazor_setki_do_raschetnoy_metki,polurasstoyanie_mezhdu_ushkami_nakladki];

module grille_face_2d() {
    difference() {
        circle(r=cap_outer_r);
        intersection() {
            circle(r=cap_inner_r);
            union() for(ix=[-grid_count:grid_count],iy=[-grid_count:grid_count])
                translate([ix*shag_setki,iy*shag_setki])
                    offset(r=skruglenie_yacheyki)
                        square([grid_hole-2*skruglenie_yacheyki,
                                grid_hole-2*skruglenie_yacheyki],center=true);
        }
    }
}

module grille_face() {
    translate([0,0,grid_bottom])
        linear_extrude(tolshchina_setki) grille_face_2d();
}

module cap_skirt() {
    // Юбка охватывает исходный корпус с боковым зазором.
    // Нижние боковые вырезы для стока воды; накладка остаётся открытой.
    difference() {
        translate([0,0,skirt_bottom])
            cylinder(r=cap_outer_r,h=grid_bottom+0.4-skirt_bottom);
        translate([0,0,skirt_bottom-eps])
            cylinder(r=cap_inner_r,h=grid_bottom+0.4-skirt_bottom+2*eps);
        for(a=[90,270]) rotate([0,0,a])
            translate([cap_inner_r-0.1,-1.0,skirt_bottom-eps])
                cube([tolshchina_stenki_nakladki+0.3,2.0,1.2+eps]);
    }
}

module cap_loop(s) {
    translate([s*polurasstoyanie_mezhdu_ushkami_nakladki-dlina_ushka/2,0,loop_h/2])
        multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
            closed_loop_local();
}

module cap_post(sx,sy) {
    // Четыре наклонные стойки снаружи корпуса; заход в крыши ушек 1,2 мм.
    z0=loop_h-1.2;
    z1=skirt_bottom+2.0;
    hull() {
        translate([sx*polurasstoyanie_mezhdu_ushkami_nakladki,sy*loop_arm_y,z0+0.35])
            cylinder(r=shirina_stoyki_nakladki/2,h=eps,$fn=48);
        translate([sx*polurasstoyanie_mezhdu_ushkami_nakladki,sy*loop_arm_y,z0])
            cylinder(r=shirina_stoyki_nakladki/2-0.35,h=eps,$fn=48);
        translate([sx*cap_post_root_x,sy*loop_arm_y,z1-0.35])
            cylinder(r=shirina_stoyki_nakladki/2,h=eps,$fn=48);
        translate([sx*cap_post_root_x,sy*loop_arm_y,z1-eps])
            cylinder(r=shirina_stoyki_nakladki/2-0.35,h=eps,$fn=48);
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
    // Решётка лежит лицевой стороной на столе.
    // Верхним частям проходов ремня требуются поддержки.
    translate([0,0,cap_top]) rotate([180,0,0]) grille_cap_installed();
}

if(vid_modeli=="nakladka") grille_cap_print();
else if(vid_modeli=="nakladka_v_sborke") grille_cap_installed();
else if(vid_modeli=="sborka") {
    holder_installed();
    grille_cap_installed();
} else if(vid_modeli=="stol") {
    translate([-polurasstoyanie_mezhdu_detalyami,0,body_print_lift])
        rotate([45,0,0]) holder_installed();
    translate([polurasstoyanie_mezhdu_detalyami,0,0]) grille_cap_print();
} else assert(false,"Неизвестный вид модели");

echo(cap_outer_diameter=2*cap_outer_r,grid_cell=grid_hole,
     bar_width=shirina_peremychki_setki,tolshchina_setki=tolshchina_setki,
     nominal_button_gap=zazor_setki_do_raschetnoy_metki,cap_total_height=cap_top,
     skirt_overlap=perehlyost_yubki,radial_clearance=bokovoy_zazor_nakladki,
     cap_loop_spacing=2*polurasstoyanie_mezhdu_ushkami_nakladki);

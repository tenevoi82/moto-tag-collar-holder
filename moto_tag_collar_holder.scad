/* Держатель Moto Tag первого поколения для кожаного ошейника, TPU 95A.
   Все размеры в миллиметрах. Наклон 45° предназначен для печати С поддержками.
   Для осмотра сборки отключите polozhenie_dlya_pechati.
   Это геометрия опубликованной версии: расчётная толщина метки 8,0 мм.
   Пользователь измерил 8,2 мм и утопление 3,5 мм; аудит — validation/MODEL_AUDIT_RU.md.
   Скруглённый диск служит условной проверкой, точный профиль Moto Tag не снят.
   Названия параметров транслитом: OpenSCAD 2021.01 не принимает кириллицу
   в идентификаторах. Описания и группы настроек — по-русски. */

/* [Размеры метки и ошейника] */
// Диаметр метки, мм
diametr_metki = 31.9;
// Расчётная толщина метки в опубликованной модели, мм
tolshchina_metki = 8.0;
// Ширина ремня ошейника, мм
shirina_osheynika = 21.5;
// Толщина ремня ошейника, мм
tolshchina_osheynika = 3.85;

/* [Посадка и зазоры] */
// Общий зазор прохода ремня по ширине, мм
zazor_remnya_po_shirine = 0.8;
// Общий зазор прохода ремня по толщине до рёбер, мм
zazor_remnya_po_tolshchine = 0.6;
// Зазор с каждой стороны метки на её максимальном диаметре, мм
bokovoy_zazor_metki = 0.2;
// Осевой припуск в формуле высоты; это НЕ измеренный свободный ход, мм
osevoy_pripusk_metki = 0.4;
// Предполагаемое скругление края метки; точный профиль не измерен, мм
predpolagaemoe_skruglenie_metki = 0.8;
// Дополнительное сужение отверстия после учёта скругления; не фактический нахлёст, мм
radialnoe_suzhenie_bortika = 0.6;
// Добавка с каждой стороны к высоте кольца; не отдельная толщина полки, мм
osevaya_dobavka_bortika = 0.9;

/* [Кольцо, ушки и стойки] */
// Толщина стенки кольца на уровне максимального диаметра метки, мм
tolshchina_stenki_koltsa = 2.0;
// Скругление наружных краёв кольца и ушек, мм
skruglenie_naruzhnyh_krayov = 1.0;
// Толщина стенки ушка, мм
tolshchina_stenki_ushka = 2.0;
// Длина ушка вдоль ремня, мм
dlina_ushka = 3.2;
// Скругление углов прохода ремня, мм
skruglenie_prohoda_remnya = 0.6;
// Фаска на входах ушка, мм
faska_vhoda_v_ushko = 0.35;
// Высота мягкого ребра с каждой стороны прохода ремня, мм
vysota_reber_prizhima = 0.25;
// Расчётный зазор под меткой после изгиба ремня, мм
zazor_nad_izognutym_remnem = 1.2;
// Расчётный радиус наружной поверхности согнутого ошейника, мм
radius_izgiba_osheynika = 40;
// Отступ центра ушка внутрь от наружного радиуса кольца, мм
otstup_ushka_ot_kraya = 5.65;
// Ширина соединительной стойки, мм
shirina_stoyki = 4.0;
// Высота захода стойки в кольцо, мм
vysota_zahoda_stoyki = 2.4;
// Направление звукового выреза: 90 или 270 градусов
ugol_okna_dinamika = 90;
// Ширина сектора звукового выреза, градусы
sektor_okna_dinamika = 50;
// Высота звукового выреза от заднего края кольца, мм
vysota_okna_dinamika = 2.4;

/* [Вид модели] */
// Включить наклон корпуса на 45 градусов для печати с поддержками
polozhenie_dlya_pechati = true;
// Показать условную метку и прямой ремень только в предварительном просмотре F5
pokazat_metku_i_remen = false;
// Количество граней окружности
kachestvo_okruzhnosti = 192;

/* [Hidden] */
$fn = kachestvo_okruzhnosti;
eps = 0.02;
bore_r = diametr_metki/2 + bokovoy_zazor_metki;
outer_r = bore_r + tolshchina_stenki_koltsa;
throat_r = bore_r - predpolagaemoe_skruglenie_metki - radialnoe_suzhenie_bortika;
mouth_bevel = 0.25;
transition_height = mouth_bevel + bore_r - throat_r; // переход под 45 градусов
ring_height = tolshchina_metki + osevoy_pripusk_metki + 2*osevaya_dobavka_bortika;
slot_w = shirina_osheynika + zazor_remnya_po_shirine;
slot_t = tolshchina_osheynika + zazor_remnya_po_tolshchine;
loop_outer_w = slot_w + 2*tolshchina_stenki_ushka;
loop_outer_h = slot_t + 2*tolshchina_stenki_ushka;
loop_x = outer_r - otstup_ushka_ot_kraya;
curve_half_span = loop_x + dlina_ushka/2;
curvature_sag = radius_izgiba_osheynika -
    sqrt(pow(radius_izgiba_osheynika,2)-pow(curve_half_span,2));
// Поднять условную заднюю поверхность над согнутым ремнём и крышами ушек.
ring_base = max(tolshchina_stenki_ushka+slot_t+zazor_nad_izognutym_remnem+curvature_sag-
                osevaya_dobavka_bortika-osevoy_pripusk_metki/2,
                loop_outer_h+0.5-osevaya_dobavka_bortika-osevoy_pripusk_metki/2);
arm_y = slot_w/2 + tolshchina_stenki_ushka/2;
arm_root_x = sqrt(pow(outer_r-0.8,2)-pow(arm_y,2));
tag_back = ring_base + osevaya_dobavka_bortika + osevoy_pripusk_metki/2;
// Нижняя точка скруглённого ушка после поворота на 45° вокруг X.
print_lift = (loop_outer_w/2 - skruglenie_naruzhnyh_krayov*(2-sqrt(2)))/sqrt(2);

assert(predpolagaemoe_skruglenie_metki >= 0 && predpolagaemoe_skruglenie_metki < tolshchina_metki/2);
assert(bokovoy_zazor_metki >= 0 && radialnoe_suzhenie_bortika > bokovoy_zazor_metki);
assert(throat_r > 0 && ring_height > 2*transition_height + 1);
assert(tolshchina_stenki_koltsa >= 1.6 && tolshchina_stenki_ushka >= 1.6 && shirina_stoyki >= 3.2);
assert(dlina_ushka > 2*faska_vhoda_v_ushko + 1);
assert(vysota_reber_prizhima >= 0 && vysota_reber_prizhima < tolshchina_stenki_ushka/2);
assert(skruglenie_naruzhnyh_krayov > 0 && skruglenie_naruzhnyh_krayov <= tolshchina_stenki_ushka/2);
assert(skruglenie_prohoda_remnya < min(slot_w,slot_t)/2);
assert(arm_y < outer_r-0.8, "Ремень слишком широк для выбранного расположения ушек");
assert(radius_izgiba_osheynika > curve_half_span+5);
assert(loop_x-dlina_ushka/2 > 5 && loop_x < outer_r);
assert(zazor_nad_izognutym_remnem >= 1.0);
assert(vysota_okna_dinamika < ring_height/2);
assert(ugol_okna_dinamika == 90 || ugol_okna_dinamika == 270,
       "Звуковой вырез должен быть сбоку, вне соединений со стойками");

module rounded_rect_2d(w,h,r) {
    offset(r=r) square([w-2*r,h-2*r],center=true);
}

module ring_outer() {
    rr = min(skruglenie_naruzhnyh_krayov,tolshchina_stenki_koltsa/2);
    rotate_extrude(convexity=10)
        polygon(concat([[0,0],[outer_r-rr,0]],
            [for(a=[-90:5:0]) [outer_r-rr+rr*cos(a),rr+rr*sin(a)]],
            [[outer_r,ring_height-rr]],
            [for(a=[0:5:90])
                [outer_r-rr+rr*cos(a),ring_height-rr+rr*sin(a)]],
            [[0,ring_height]]));
}

// Передняя кромка замкнута; в задней затем вырезается звуковой сектор.
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
    translate([0,0,-eps]) linear_extrude(vysota_okna_dinamika+eps)
        polygon(concat([[0,0]], [for(a=[ugol_okna_dinamika-sektor_okna_dinamika/2:
            1:ugol_okna_dinamika+sektor_okna_dinamika/2])
            [(outer_r+3)*cos(a),(outer_r+3)*sin(a)]]));
}

module ring_only(acoustic_window=true) {
    difference() {
        ring_outer();
        tag_void();
        if(acoustic_window) speaker_cut();
    }
}

// Профиль XY переходит в плоскость YZ сборки; выдавливание Z — вдоль X.
module closed_loop_local() {
    $fn = 64;
    b = faska_vhoda_v_ushko;
    union() {
    difference() {
        hull() {
            for(z=[b,dlina_ushka-b-eps]) translate([0,0,z])
                linear_extrude(eps)
                    rounded_rect_2d(loop_outer_w,loop_outer_h,skruglenie_naruzhnyh_krayov);
            for(z=[0,dlina_ushka-eps]) translate([0,0,z])
                linear_extrude(eps)
                    rounded_rect_2d(loop_outer_w-2*b,loop_outer_h-2*b,
                                    skruglenie_naruzhnyh_krayov-b);
        }
        translate([0,0,-eps]) linear_extrude(dlina_ushka+2*eps)
            rounded_rect_2d(slot_w,slot_t,skruglenie_prohoda_remnya);
        // Фаски обоих входов; в середине сохраняется полный профиль прохода.
        for(mirror_end=[false,true])
            translate([0,0,mirror_end ? dlina_ushka : 0])
                scale([1,1,mirror_end ? -1 : 1]) hull() {
                    translate([0,0,-eps]) linear_extrude(eps)
                        rounded_rect_2d(slot_w+2*b,slot_t+2*b,skruglenie_prohoda_remnya+b);
                    translate([0,0,b]) linear_extrude(eps)
                        rounded_rect_2d(slot_w,slot_t,skruglenie_prohoda_remnya);
                }
    }
    // Широкие скруглённые рёбра из TPU. Тестовый калибр использует тот же профиль.
    r = 0.8;
    if(vysota_reber_prizhima > 0)
        for(v=[-slot_t/2+vysota_reber_prizhima-r,
               slot_t/2-vysota_reber_prizhima+r])
            hull() for(u=[-slot_w/2+1.5,slot_w/2-1.5])
                translate([u,v,dlina_ushka/2]) sphere(r=r,$fn=32);
    }
}

function holder_outer_radius() = outer_r;
function loop_profile_height() = loop_outer_h;
// Общие размеры сборки для накладки, удерживаемой ремнём.
// Возвращает размеры; самостоятельно геометрию не меняет.
function holder_geometry() = [outer_r,ring_base,ring_height,
    tag_back+tolshchina_metki,loop_outer_h,loop_x,dlina_ushka,arm_y,print_lift];

module belt_loop(s=1) {
    translate([s*loop_x-dlina_ushka/2,0,loop_outer_h/2])
        multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
            closed_loop_local();
}

module bridge_arm(sx,sy) {
    $fn = 48;
    // Четыре скруглённые стойки; заход в стенку/крышу ушка на 1,2 мм.
    arm_z = loop_outer_h-1.2;
    arm_h = ring_base+vysota_zahoda_stoyki-arm_z;
    translate([0,0,arm_z]) hull() {
        for(x=[sx*arm_root_x,sx*loop_x])
            translate([x,sy*arm_y,0]) {
                for(z=[0.35,arm_h-0.35-eps])
                    translate([0,0,z]) cylinder(r=shirina_stoyki/2,h=eps);
                for(z=[0,arm_h-eps])
                    translate([0,0,z]) cylinder(r=shirina_stoyki/2-0.35,h=eps);
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
        // Полость вычитается после объединения, чтобы стойки не заходили в метку.
        translate([0,0,ring_base]) {
            tag_void();
            speaker_cut();
        }
    }
}

module tag_reference() {
    e = predpolagaemoe_skruglenie_metki;
    translate([0,0,tag_back])
        if(e>0) rotate_extrude() polygon(concat(
            [[0,0],[diametr_metki/2-e,0]],
            [for(a=[-90:5:0]) [diametr_metki/2-e+e*cos(a),e+e*sin(a)]],
            [[diametr_metki/2,tolshchina_metki-e]],
            [for(a=[0:5:90])
                [diametr_metki/2-e+e*cos(a),tolshchina_metki-e+e*sin(a)]],
            [[0,tolshchina_metki]]));
        else cylinder(d=diametr_metki,h=tolshchina_metki);
}

module references() {
    %color([0.2,0.6,0.9,0.45]) tag_reference();
    %color([0.45,0.22,0.1,0.45])
        translate([-34,-shirina_osheynika/2,tolshchina_stenki_ushka+zazor_remnya_po_tolshchine/2])
            cube([68,shirina_osheynika,tolshchina_osheynika]);
}

module output_model() {
    holder_installed();
    if(pokazat_metku_i_remen && $preview) references();
}

if(polozhenie_dlya_pechati)
    translate([0,0,print_lift]) rotate([45,0,0]) output_model();
else output_model();

echo(bore_diameter=2*bore_r, lip_throat_diameter=2*throat_r,
     collar_slot=[slot_w,slot_t], ring_height=ring_height,
     installed_height=ring_base+ring_height,
     rear_air_gap_min=tag_back-(tolshchina_stenki_ushka+slot_t),
     curve_sag=curvature_sag, minimum_curved_air_gap=tag_back-
        (tolshchina_stenki_ushka+slot_t+curvature_sag),
     nominal_equator_stretch_percent=100*(diametr_metki/(2*throat_r)-1));

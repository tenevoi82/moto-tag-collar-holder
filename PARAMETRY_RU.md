# Параметры OpenSCAD по-русски

Этот справочник описывает исходную V1 в корне проекта. Новые параметры задней опоры и изменённые настройки V2 перечислены в [инструкции V2](v2/README.md#настройки-openscad).

Группы и описания в настройках — на русском. Имена переменных — транслитом: установленный OpenSCAD 2021.01 отвергает кириллицу в идентификаторах. В формулах сохранены внутренние имена функций и промежуточных величин.

Перевод не меняет геометрию опубликованных STL/3MF. Измеренные отклонения разобраны отдельно в [аудите модели](validation/MODEL_AUDIT_RU.md).

| Было | Стало | Значение настройки |
|---|---|---|
| `tag_diameter` | `diametr_metki` | Диаметр метки, мм |
| `tag_thickness` | `tolshchina_metki` | Расчётная толщина метки в опубликованной модели, мм |
| `collar_width` | `shirina_osheynika` | Ширина ремня ошейника, мм |
| `collar_thickness` | `tolshchina_osheynika` | Толщина ремня ошейника, мм |
| `collar_width_clearance` | `zazor_remnya_po_shirine` | Общий зазор прохода ремня по ширине, мм |
| `collar_thickness_clearance` | `zazor_remnya_po_tolshchine` | Общий зазор прохода ремня по толщине до рёбер, мм |
| `tag_radial_clearance` | `bokovoy_zazor_metki` | Зазор с каждой стороны метки на её максимальном диаметре, мм |
| `tag_axial_clearance` | `osevoy_pripusk_metki` | Осевой припуск в формуле высоты; это НЕ измеренный свободный ход, мм |
| `tag_edge_radius_assumed` | `predpolagaemoe_skruglenie_metki` | Предполагаемое скругление края метки; точный профиль не измерен, мм |
| `retention_lip` | `radialnoe_suzhenie_bortika` | Дополнительное сужение отверстия после учёта скругления; не фактический нахлёст, мм |
| `retention_lip_height` | `osevaya_dobavka_bortika` | Добавка с каждой стороны к высоте кольца; не отдельная толщина полки, мм |
| `ring_wall_thickness` | `tolshchina_stenki_koltsa` | Толщина стенки кольца на уровне максимального диаметра метки, мм |
| `edge_radius` | `skruglenie_naruzhnyh_krayov` | Скругление наружных краёв кольца и ушек, мм |
| `loop_wall` | `tolshchina_stenki_ushka` | Толщина стенки ушка, мм |
| `loop_length` | `dlina_ushka` | Длина ушка вдоль ремня, мм |
| `slot_corner_radius` | `skruglenie_prohoda_remnya` | Скругление углов прохода ремня, мм |
| `loop_entry_bevel` | `faska_vhoda_v_ushko` | Фаска на входах ушка, мм |
| `grip_rib_height` | `vysota_reber_prizhima` | Высота мягкого ребра с каждой стороны прохода ремня, мм |
| `vent_gap` | `zazor_nad_izognutym_remnem` | Расчётный зазор под меткой после изгиба ремня, мм |
| `collar_bend_radius` | `radius_izgiba_osheynika` | Расчётный радиус наружной поверхности согнутого ошейника, мм |
| `loop_inset` | `otstup_ushka_ot_kraya` | Отступ центра ушка внутрь от наружного радиуса кольца, мм |
| `arm_width` | `shirina_stoyki` | Ширина соединительной стойки, мм |
| `arm_height` | `vysota_zahoda_stoyki` | Высота захода стойки в кольцо, мм |
| `speaker_angle` | `ugol_okna_dinamika` | Направление звукового выреза: 90 или 270 градусов |
| `speaker_angle_width` | `sektor_okna_dinamika` | Ширина сектора звукового выреза, градусы |
| `speaker_window_height` | `vysota_okna_dinamika` | Высота звукового выреза от заднего края кольца, мм |
| `print_orientation` | `polozhenie_dlya_pechati` | Включить наклон корпуса на 45 градусов для печати с поддержками |
| `show_reference` | `pokazat_metku_i_remen` | Показать условную метку и прямой ремень только в предварительном просмотре F5 |
| `quality` | `kachestvo_okruzhnosti` | Количество граней окружности |
| `grid_pitch` | `shag_setki` | Шаг ячеек решётки, мм |
| `grid_bar_width` | `shirina_peremychki_setki` | Ширина перемычки решётки, мм |
| `grid_thickness` | `tolshchina_setki` | Толщина решётки, мм |
| `grid_hole_radius` | `skruglenie_yacheyki` | Скругление углов ячейки, мм |
| `button_face_gap` | `zazor_setki_do_raschetnoy_metki` | Зазор до условной передней поверхности метки; не измеренный зазор до кнопки, мм |
| `cap_radial_clearance` | `bokovoy_zazor_nakladki` | Зазор с каждой стороны между юбкой накладки и кольцом, мм |
| `cap_wall` | `tolshchina_stenki_nakladki` | Толщина стенки юбки накладки, мм |
| `cap_skirt_overlap` | `perehlyost_yubki` | Перекрытие накладкой верхней части кольца, мм |
| `cap_loop_x` | `polurasstoyanie_mezhdu_ushkami_nakladki` | Половина расстояния между центрами ушек накладки, мм |
| `cap_post_width` | `shirina_stoyki_nakladki` | Ширина стойки накладки, мм |
| `output_part` | `vid_modeli` | Выбор детали или сборки |
| `plate_half_spacing` | `polurasstoyanie_mezhdu_detalyami` | Половина расстояния между деталями на печатном столе, мм |
| `coupon_gap` | `promezhutok_mezhdu_obraztsami` | Расстояние между тестовым кольцом и калибром ушка, мм |

`vid_modeli`: `stol` — обе детали для печати, `nakladka` — только накладка для печати, `sborka` — сборка для осмотра, `nakladka_v_sborke` — накладка в сборочных координатах. Для сборки и метки параметры берутся из основного SCAD; меняйте их там и сохраняйте файл.

Раздел `[Hidden]` — служебная команда OpenSCAD, поэтому её название оставлено на английском. Кнопки `true` и `false` — встроенные значения языка.

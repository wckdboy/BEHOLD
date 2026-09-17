// BEHOLD Utilities — Danish wall stack (millimetres)
// Feature-flagged helper. Not structural engineering.
// MinAltan A/S section drawings are reference only (vejledende).

width = 4000;
height = 2800;
exterior = 108;
insulation = 359;
interior = 13;
door = false;
door_w = 900;
door_h = 2100;

module danish_wall() {
    difference() {
        union() {
            color("firebrick") cube([width, exterior, height]);
            translate([0, exterior, 0])
                color("khaki") cube([width, insulation, height]);
            translate([0, exterior + insulation, 0])
                color("white") cube([width, interior, height]);
        }
        if (door) {
            translate([(width - door_w) / 2, -1, 0])
                cube([door_w, exterior + insulation + interior + 2, door_h]);
        }
    }
}

danish_wall();

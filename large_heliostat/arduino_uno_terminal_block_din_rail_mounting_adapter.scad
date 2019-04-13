EPSILON = 0.005;
CLIP_H = 68.6;
//this clip can be easily de-mounted without a screw driver
//holes are extremly "long", because i'm lazy
{
difference() {
		union() {
			linear_extrude(height=CLIP_H, center=false, convexity=5) {
				translate([0,22,0]) import(file="DIN_miki.dxf", layer="0", $fn=65);
			}
		}
		union() {
            // ll 
			translate([-70,3+2.5,14]) // z=(68.6-14)/2
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            // lr
            translate([-70,3+2.5+5.1,14+1.3+50.8]) 
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            
            // ur
            translate([-70,3+2.5+5.1+27.9,14+1.3+50.8]) 
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            
			//pre-holes for PCB mounting
            /*
			translate([-70,15, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
            
			translate([-70,10, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
			translate([-70,5, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
			translate([-70,0, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
			translate([-70,-5, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
			translate([-70,-10, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
			translate([-70,-15, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1, r2 = 1, center = true);
                    */
/*
			//big holes for screw-driver
			translate([0,10, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 50, r1 = 3, r2 = 3, center = true);
			translate([0,0, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 50, r1 = 3, r2 = 3, center = true);
			translate([0,-10, 0])
				rotate(90, [0, 1, 0])
					cylinder(h = 50, r1 = 3, r2 = 3, center = true);
*/
		}
	}
}


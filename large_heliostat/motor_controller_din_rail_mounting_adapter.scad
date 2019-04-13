EPSILON = 0.005;
CLIP_H = 92;
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
			translate([-70,22.5, 3]) // z=(68.6-14)/2
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            // lr
           translate([-70,22.5, 3+87]) // z=(68.6-14)/2
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
         	
		}
	}
}


EPSILON = 0.005;
CLIP_H = 55;
//this clip can be easily de-mounted without a screw driver
//holes are extremly "long", because i'm lazy
{
difference() {
		union() {
			linear_extrude(height=CLIP_H, center=true, convexity=5) {
				import(file="DIN_miki.dxf", layer="0", $fn=128);
			}
		}
		union() {
            
			translate([-70,0, 22.5])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            translate([-70,0, -22.5])
				rotate(90, [0, 1, 0])
					cylinder(h = 100, r1 = 1.8, r2 = 1, center = true, $fn=25);
            
		}
	}
}


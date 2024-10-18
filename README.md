## bin_composite

Combines two SNES graphics files into a composite image, with one image occluding (on top of) the other.

Use like `bin_composite.exe background.bin top.bin output.bin`

## bin_roll

Shifts pixels in an input SNES graphic file, while copying pixels shifted out of the image to the other side.

Use like `bin_roll.exe  -x 5 -y 0 input.bin output.bin` to shift 5 pixels left.

# >>> set K with poles = [0 -10 -5+1j -5-1j]
# M11 K(0,-0.25,-0.44,-0.05,0,0,0,-0.25,-0.44,-0.05,0,0)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2
# M2 S2
# M2 S3

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + NEW MOI + Iyy referenced to cg)
# M11 K(-0.2019,-0.2185,-0.3525,-0.0337,-0.0448,-0.0321,-0.2019,-0.2185,-0.3525,-0.0337,-0.0448,-0.0321)
# M10 E(1,1,1,0,1,0,1,1,1)

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + HALVED MOI + Iyy referenced to wa)
# M11 K(-0.2269,-0.2433,-0.3958,-0.0458,-0.0323,-0.0220,-0.2269,-0.2433,-0.3958,-0.0458,0.0323,0.0220)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + HALVED MOI + Iyy referenced to cg)
# M11 K(-0.1599,-0.1766,-0.3336,-0.0314,-0.0323,-0.0220,-0.1599,-0.1766,-0.3336,-0.0314,0.0323,0.0220)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + HALVED MOI NEW POLES 1 + Iyy referenced to cg)
# M11 K(-0.1108,-0.1442,-0.3279,-0.0355,-0.0323,-0.0220,-0.1108,-0.1442,-0.3279,-0.0355,0.0323,0.0220)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + HALVED MOI NEW POLES 2 + Iyy referenced to cg)
# M11 K(0,-0.1772,-0.4292,-0.0585,0,-0.0057,0,-0.1772,-0.4292,-0.0585,0,0.0057)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + VARIABLE MOI + Iyy referenced to cg [from now always])
# %% see TWIPR_STATE_FEEDBACK/SF_TUNING.txt for further information
# exp1
# M11 K(-0.2060,-0.2225,-0.3623,-0.0366,-0.0403,-0.0285,-0.2060,-0.2225,-0.3623,-0.0366,0.0403,0.0285)
# exp2
# M11 K(-0.2167,-0.2332,-0.3444,-0.0357,-0.0403,-0.0285,-0.2167,-0.2332,-0.3444,-0.0357,0.0403,0.0285)
# exp3
# M11 K(-0.1969,-0.2134,-0.3829,-0.0377,-0.0394,-0.0277,-0.1969,-0.2134,-0.3829,-0.0377,0.0394,0.0277)
# exp4
# M11 K(-0.1933,-0.2098,-0.3932,-0.0384,-0.0394,-0.0277,-0.1933,-0.2098,-0.3932,-0.0384,0.0394,0.0277)
# exp5
# M11 K(-0.1902,-0.2067,-0.4035,-0.0391,-0.0394,-0.0277,-0.1902,-0.2067,-0.4035,-0.0391,0.0394,0.0277)
# exp6
# M11 K(-0.1865,-0.2030,-0.4190,-0.0402,-0.0394,-0.0277,-0.1865,-0.2030,-0.4190,-0.0402,0.0394,0.0277)
# exp7
# M11 K(-0.1821,-0.1986,-0.4449,-0.0422,-0.0394,-0.0277,-0.1821,-0.1986,-0.4449,-0.0422,0.0394,0.0277)
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# exp8
# M11 K(0,-0.1562,-0.4126,-0.0488,0,-0.0079,0,-0.1562,-0.4126,-0.0488,0,0.0079)
# exp9
# M11 K(0,-0.1459,-0.4782,-0.0545,0,-0.0079,0,-0.1459,-0.4782,-0.0545,0,0.0079)
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# exp10 (PREFERRED CONFIGURATION)
G2 K(0,-0.1717,-0.3880,-0.0391,0,-0.0119,0,-0.1717,-0.3880,-0.0391,0,0.0119)
# test
# G2 K(0,-0.1562,-0.4126,-0.0488,0,-0.0079,0,-0.1562,-0.4126,-0.0488,0, 0.0079)
# exp11
# M11 K(0,-0.1601,-0.4507,-0.0437,0,-0.0119,0,-0.1601,-0.4507,-0.0437,0,0.0119)
# stable poles similar to exp 10 (!)
# G2 K(-0.2470,-0.2472,-0.4001,-0.0400,-0.0394,-0.0277,-0.2470,-0.2472,-0.4001,-0.0400,0.0394,0.0277)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %% VEL TUNING XDOT (with SF config 10)
# exp1
# M12 P-0.103770064514607 I-0.454839158523993 D-0.0009922167292936669
# exp2
# G3 P-0.051885032257303 I-0.227419579261997 D-0.0004961083646468334
# exp3
# M12 P-0.105478569866781 I-0.315008062084906 D-0.005105363341365
# exp5
# M12 P-0.081933964408743 I-0.274621842183765 D-0.0007918774598690570
# exp6
# M12 P-0.06 I-0.25 D-0.0006
# exp7 (PREFERRED CONFIGURATION)
# G3 P-0.12 I-0.5 D-0.0012
# test: 20.12
# G3 P-0.240465999049065 I-0.625102758255451 D-0.023125756499636
# G3 P-0.1 I-0.2 D-0.0030591
# continuing work with the experiments: 30.01 (this is the configuration for the new plots)
G3 P-0.102574414285258 I-0.300711415250027 D-0.0009956730013275788

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %% VEL TUNING PSIDOT (with SF config 10)
# exp 2
# G4 P0 I0 D0.001
# G4 M13 P-0.032047451524581 I-0.122549714316250 D-0.0003082195438141891
# 04.01: new psidot controller (this is the configuration for the new plots)
G4 P-0.026696398913630 I-0.090151144347773 D-0.0002579488747015259

# ->
M4
G0 E(0,0,0,0,0,1,0,0,0)
M1 S2

# °°°°°°°°°°°
# DEBUG
# M5 T1
# M1 S1
# M5 T0.2
# M1 S3
# M5 T0.2
# M1 S2
# °°°°°°°°°°°

# M2 S3
# NOT IMPLEMENTED
# G1 X1
# G0 T5 (BBB_PY MSG HANDLER SLEEP FOR 5 SEC)
# G1 X0
# TODO: ATTENTION G-CODES HAVE BEEN CHANGED




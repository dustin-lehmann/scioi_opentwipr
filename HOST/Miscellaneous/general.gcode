# config.txt == template for automated command transmission
# -> Use <#> to comment out lines
# -> See "HOST_GCodeParser.py" & "host_gcodes.txt" for further information

# >>> poles = [-3+1i -3-1i -5+1i -5-1i]
# M11 K(-0.24,-0.26,-0.40,-0.05,0,0,-0.24,-0.26,-0.40,-0.05,0,0)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [0 -10 -5+1j -5-1j]
# M11 K(0,-0.25,-0.44,-0.05,0,0,0,-0.25,-0.44,-0.05,0,0)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (MATLAB pole placement which creates a weird coupling between the states])
# M11 K(-0.3493,-0.3611,-0.4857,-0.0573,-0.0923,-0.0473,0.1603,0.0954,-0.1585,-0.0124,0.0922,0.0467)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment)
# M11 K(-0.2428,-0.2592,-0.4026,-0.0467,0.0358,0.0248,-0.2428,-0.2592,-0.4026,-0.0467,0.0358,0.0248)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# FIXME >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + heavy wheels + Iyy referenced to wa)
# M11 K(-0.2837,-0.2999,-0.4174,-0.0488,-0.0448,-0.0321,-0.2837,-0.2999,-0.4174,-0.0488,-0.0448,-0.0321)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + NEW_MOI + Iyy referenced to cg)
# M11 K(-0.2019,-0.2185,-0.3525,-0.0337,-0.0448,-0.0321,-0.2019,-0.2185,-0.3525,-0.0337,-0.0448,-0.0321)
# M10 E(1,1,1,0,1,0,1,1,1)
# M1 S2

# >>> poles = [-3+1i -3-1i -5+1i -5-1i -2-1i -2+1i] (pole placement with eigenstructure assignment + HALVED MOI + Iyy referenced to wa)
G2 K(-0.2269,-0.2433,-0.3958,-0.0458,-0.0323,-0.0220,-0.2269,-0.2433,-0.3958,-0.0458,0.0323,0.0220)
G0 E(0,0,0,0,0,0,0,0,0)
# TODO: ATTENTION G-CODES HAVE BEEN CHANGED
# DEBUGGING SEQUENCE HANDLER
M1 S2
M5 T0.2
M2 S1
M5 T0.2
M71
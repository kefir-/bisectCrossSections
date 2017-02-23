from FreeCAD import Base
import Draft
import Part
import time
App=FreeCAD

def bisectCrossSections(obj, layerThickness, layerLocation=0.5): 
    '''bisectSliceWire(obj, layerThickness, layerLocation) splits an object
       into wires at layerThickness intervals along the Z axis, and distributes
       the wire shapes on a plane. If you want to laser cut a 3-dimensional
       object in 4mm plywood, run bisectSliceWire(object, 4), and you will get
       the laser cutting paths necessary.

       layerLocation is a range from [0.0, 1.0] that specifies where in each
       layerThickness segment the wire should cut, where 0.0 is the bottom,
       0.5 is the center, and 1.0 is the top. Values outside the accepted range
       are truncated.

       This script was initially based on slicePart() from the script available on
       http://freecadbuch.de/doku.php?id=blog:schnittmodell_eines_hauses_fuer_den_laser-schneider

       This script uses an optimisation for complex objects that includes
       cutting the original object into two, and then cutting each segment in
       two, repeating until the segments are suitably small. This has resulted
       in a time optimisation on the order of 50-60x on my laptop, for a freecad
       object that was created from a mesh, as shown in
       https://www.youtube.com/watch?v=avVNfIswkMU
    '''
    layerLocation=max(0.0, layerLocation) # enforce sensible limits
    layerLocation=min(1.0, layerLocation)
    sections = []   
    workSections = [obj]
    i = 0
    while len(workSections) > 0:
        o = workSections.pop(0)
        b = o.Shape.BoundBox
        lx = b.XLength
        ly = b.YLength
        lz = b.ZLength

        if lz < layerThickness:
            sections.append(o)
            continue

        label_boxbothalf = "box_bottom_half_{0}".format(i)
        label_bothalf = "bottom_half_{0}".format(i)
        label_tophalf = "top_half_{0}".format(i)

        # create bottom half with Intersection boolean op
        s=App.ActiveDocument.addObject("Part::Box",label_boxbothalf)
        s.Placement = App.Placement(App.Vector(b.XMin - 1,b.YMin - 1,b.ZMin - 1),App.Rotation(App.Vector(0,0,1),0))
        s.Length = lx + 2
        s.Width = ly + 2
        s.Height = (lz/2) + 1
        bottom_half = App.activeDocument().addObject("Part::MultiCommon",label_bothalf)
        bottom_half.Shapes = [o, s]

        # create top half with Difference boolean op
        top_half = App.activeDocument().addObject("Part::Cut",label_tophalf)
        top_half.Base = o
        top_half.Tool = s

        App.ActiveDocument.recompute()

        if bottom_half.Shape.BoundBox.ZLength > layerThickness*2:
            workSections.append(bottom_half)
        else:
            sections.append(bottom_half)

        if top_half.Shape.BoundBox.ZLength > layerThickness*2:
            workSections.append(top_half)
        else:
            sections.append(top_half)

        i = i + 1
 
    g2=App.ActiveDocument.addObject("App::DocumentObjectGroup",str(obj.Label) + "_Slices")

    total_zmin = obj.Shape.BoundBox.ZMin
    total_zmax = obj.Shape.BoundBox.ZMax
    lx = obj.Shape.BoundBox.XLength + 5
    ly = obj.Shape.BoundBox.YLength + 5

    out_x=0
    out_y=0
    start_z = total_zmin + (layerThickness * layerLocation)
    step = layerThickness
    total_step = step
    current_z = start_z + total_step
    while current_z <= total_zmax:
        # Find the correct section in sections[]
        for section in sections:
            if section.Shape.BoundBox.ZMin <= current_z and section.Shape.BoundBox.ZMax >= current_z:
                try:
                    wires = list()
                    for i in section.Shape.slice(FreeCAD.Base.Vector(0,0,1),current_z):
                        wires.append(i)
                    comp = Part.Compound(wires)
                    layer = FreeCAD.ActiveDocument.addObject("Part::Feature", "MyLayer")
                    layer.Shape = comp
                    layer.purgeTouched()
                    layer.Placement.Base = FreeCAD.Vector(out_x, out_y, -current_z)
                    out_x = out_x + lx

                    if out_x > 400:
                        out_x = 0
                        out_y = out_y + ly
                    g2.addObject(layer)

                except Exception as e:
                    print "Caught exception:", repr(e)
        total_step += step
        current_z = start_z + total_step

    for section in sections:
        section.ViewObject.Visibility = False

    App.activeDocument().recompute()

#start = time.time()
bisectCrossSections(App.ActiveDocument.Solid, 4)
#end = time.time()
#print "Total time taken before recompute:", end-start, "seconds"
#App.activeDocument().recompute()
#end = time.time()
#print "Total time taken after recompute:", end-start, "seconds"


start = time.time()
end = time.time()
print "Time to delete sections:", end-start, "seconds"




def bisectSlicePart(obj, layerThickness, layerLocation=0.5): 
    '''bisectSlicePart(obj, layerThickness, layerLocation) splits an object
       into that are layerThickness millimeters thick
    '''
    # fullShape=obj.Shape
    layerLocation=max(0.0, layerLocation) # enforce sensible limits
    layerLocation=min(1.0, layerLocation)
    sections = []   
    # sectionsBaseZ = []
    workSections = [obj]
    # TODO: Specialcase for obj.ZLength <= layerThickness
    i = 0
    while len(workSections) > 0:
        o = workSections.pop(0)
        shape = o.Shape
        b=shape.BoundBox
        lx=b.XLength
        ly=b.YLength
        lz=b.ZLength
        label_boxbothalf = "box_bottom_half_{0}".format(i)
        label_bothalf = "bottom_half_{0}".format(i)
        label_boxtophalf = "box_top_half_{0}".format(i)
        label_tophalf = "top_half_{0}".format(i)

        # create bottom half with Intersection boolean op
        s=App.ActiveDocument.addObject("Part::Box",label_boxbothalf)
        s.Placement = App.Placement(App.Vector(b.XMin - 1,b.YMin - 1,b.ZMin - 1),App.Rotation(App.Vector(0,0,1),0))
        s.Length = lx + 2
        s.Width = ly + 2
        s.Height = (lz/2) + 1
        bottom_half = App.activeDocument().addObject("Part::MultiCommon",label_bothalf)
        bottom_half.Shapes = [o, s]

        # create top half with Difference boolean op
        top_half = App.activeDocument().addObject("Part::Cut",label_tophalf)
        top_half.Base = o
        top_half.Tool = s

        # o.Shape.Visibility = False
        App.ActiveDocument.recompute()

        if bottom_half.Shape.BoundBox.ZLength > layerThickness*2:
            workSections.append(bottom_half)
        else:
            sections.append(bottom_half)

        if top_half.Shape.BoundBox.ZLength > layerThickness*2:
            workSections.append(top_half)
        else:
            sections.append(top_half)

        i = i + 1


    print "Sections done, start getting perimeters.."
    g2=App.ActiveDocument.addObject("App::DocumentObjectGroup",str(obj.Label) + "_Slices")

    total_zmin = obj.Shape.BoundBox.ZMin
    total_zmax = obj.Shape.BoundBox.ZMax
    lx = obj.Shape.BoundBox.XLength + 5
    ly = obj.Shape.BoundBox.YLength + 5

    out_x=0
    out_y=0
    start_z = total_zmin + (layerThickness * layerLocation)
    step = layerThickness
    total_step = step
    current_z = start_z + total_step
    while current_z <= total_zmax:
        # Find the correct section in sections[]
        for section in sections:
            if section.Shape.BoundBox.ZMin <= current_z and section.Shape.BoundBox.ZMax >= current_z:
                try:
                    wires = list()
                    for i in section.Shape.slice(FreeCAD.Base.Vector(0,0,1),current_z):
                        wires.append(i)
                    comp = Part.Compound(wires) # necessary?
                    layer = FreeCAD.ActiveDocument.addObject("Part::Feature", "MyLayer")
                    layer.Shape = comp
                    layer.purgeTouched()
                    # del comp
                    # del wires
                    t = FreeCAD.ActiveDocument.addObject("Part::Extrusion", "Extrude")
                    t.Base = layer
                    t.Dir = (0, 0, layerThickness)
                    t.Solid = True
                    t.Placement.Base=FreeCAD.Vector(out_x, out_y, -current_z)
                    out_x = out_x + lx
                    if out_x > 400:
                        out_x = 0
                        out_y = out_y + ly
                    g2.addObject(t)
                except Exception as e:
                    print "Caught exception:", repr(e)
        total_step += step
        current_z = start_z + total_step
        print "current_z:", current_z









#   return sections
#   g2=App.ActiveDocument.addObject("App::DocumentObjectGroup",str(obj.Label) + "_Slices")
# s = bisectSlicePart_ketil(App.ActiveDocument.Solid, 4)


start = time.time()
bisectSlicePart(App.ActiveDocument.Solid, 4, 0.5)
end = time.time()
print "Total time taken before recompute:", end-start, "seconds"
App.activeDocument().recompute()
end = time.time()
print "Total time taken after recompute:", end-start, "seconds"





def slicePart(ob):
    shape=ob.Shape
    g2=App.ActiveDocument.addObject("App::DocumentObjectGroup",str(ob.Label) + "_Slices")
    b=shape.BoundBox
    print shape
    lx=b.XMax-b.XMin+5
    ly=b.YMax-b.YMin+5
    dh=4 # mm thickness per step
    h=b.ZMin + (dh / 2) # start halfway up the first step
    l=0
    bb=0
    while h < b.ZLength:
        # print h
        try:
            wires=list()
            for i in shape.slice(Base.Vector(0,0,1),h):
                wires.append(i)
            comp=Part.Compound(wires)
            slice=FreeCAD.ActiveDocument.addObject("Part::Feature","MySlice")
            slice.Shape=comp
            slice.purgeTouched()
#           del comp,wires
            t=FreeCAD.ActiveDocument.addObject("Part::Extrusion","Extrude")
            t.Base = slice
            t.Dir = (0,0,dh)
            t.Solid = True
            t.Placement.Base=FreeCAD.Vector(l,bb,-h)
            l += lx
            if l >400:
                l=0
                bb +=ly
            g2.addObject(t)
        except:
            print "FEHLER"
        h += dh
    # del shape
# main 


slicePart(App.ActiveDocument.Solid)
App.activeDocument().recompute()


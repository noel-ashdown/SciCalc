# ==============================================================================
# SciCalc.py  -  Scientific Calculator Add-In for Autodesk Fusion
# Version 1.2.0
# ------------------------------------------------------------------------------
# Registers a "Scientific Calculator" button in the Inspect panel toolbar.
# When clicked, opens calculator.html as a docked palette on the right side.
# A background polling thread reads the active Fusion selection every 0.4 s
# and writes geometry values (lengths, radii, areas, etc.) to sel.json in
# %TEMP%, which the HTML palette reads via XHR to populate the Selection panel.
# ==============================================================================

import adsk.core, adsk.fusion, os, json, threading, struct, zlib

# --- Constants -----------------------------------------------------------
PAL = "sciCalcPalette_addin_v1"  # Unique ID for the palette window
CMD = "SciCalcOpenCmd"            # Unique ID for the toolbar command button

# --- Module-level state --------------------------------------------------
# All event handlers are stored here to prevent Python garbage collection.
# Fusion requires handlers to remain alive for events to fire.
_h     = []       # Active event handler references
_timer = [None]   # Background polling timer (wrapped in list for mutability)
_prev  = ['']   # Last written selection JSON (used to skip unchanged writes)

def _safe(s):
    """Escape double quotes in a string for safe embedding in JSON."""
    return str(s).replace(chr(34), chr(39))

def _aw(path, data):
    """Atomic file write - write to .tmp then rename.
    Prevents the HTML palette reading a half-written file."""
    tmp = path + ".tmp"
    open(tmp, "w", encoding="utf-8").write(data)
    try:
        os.remove(path)
    except:
        pass
    os.rename(tmp, path)

def _mkpng(sz, r, g, b):
    """Generate a minimal solid-colour PNG of size sz x sz pixels.
    Used as a fallback icon if SVG files are unavailable."""
    def ck(n, d):
        return struct.pack(">I", len(d)) + n + d + struct.pack(">I", zlib.crc32(n + d) & 0xffffffff)
    rows = b"\x00".join(b"\x00" + bytes([r, g, b]) * sz for _ in range(sz))
    return (b"\x89PNG\r\n\x1a\n"
            + ck(b"IHDR", struct.pack(">IIBBBBB", sz, sz, 8, 2, 0, 0, 0))
            + ck(b"IDAT", zlib.compress(rows))
            + ck(b"IEND", b""))
# --- Event Handlers ------------------------------------------------------

class _HH(adsk.core.HTMLEventHandler):
    """Handles messages sent from the calculator HTML palette back to Python.
    Currently handles the "sv" (save variables) action, which writes the
    current variable store to vars.json for persistence."""
    def __init__(self, vp):
        super().__init__()
        self.vp = vp  # Path to vars.json

    def notify(self, args):
        try:
            ev = adsk.core.HTMLEventArgs.cast(args)
            ui = adsk.core.Application.get().userInterface
            base = os.path.dirname(os.path.realpath(__file__))
            if ev.action == "sv":
                _aw(self.vp, ev.data)
            elif ev.action == "saveHist":
                _aw(os.path.join(base, "history.json"), ev.data)
            elif ev.action == "saveVars":
                _aw(os.path.join(base, "variables.json"), ev.data)
            elif ev.action == "openHelp":
                # Open help.html as a Fusion palette
                help_url = "file:///" + os.path.join(base, "help.html").replace("\\", "/")
                help_pal = ui.palettes.itemById("sciCalcHelp")
                if help_pal:
                    help_pal.isVisible = True
                else:
                    hp = ui.palettes.add("sciCalcHelp", "SciCalc Help", help_url, True, True, True, 700, 800)
                    hp.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateFloating
            elif ev.action == "saveBookmarks":
                _aw(os.path.join(base, "bookmarks.json"), ev.data)
            elif ev.action == "saveHistFile":
                # Save history CSV to the SciCalc folder
                import datetime
                fname = "history_export_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
                _aw(os.path.join(base, fname), ev.data)
            elif ev.action == "saveSettings":
                _aw(os.path.join(base, "settings.json"), ev.data)
        except:
            pass

class _EH(adsk.core.CommandEventHandler):
    """Handles the execute event for the calculator command.
    Called when the toolbar button is clicked and the command fires.
    Opens the calculator palette."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            _show_palette()
        except Exception as e:
            adsk.core.Application.get().userInterface.messageBox(str(e))

class _CCH(adsk.core.CommandCreatedEventHandler):
    """Handles the commandCreated event for the toolbar button.
    Fusion fires this when the button is clicked, before executing the command.
    We connect the execute handler here, which is the required Fusion pattern."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # Remove stale _EH handlers before adding new one
        global _h
        _h = [x for x in _h if not isinstance(x, _EH)]
        # Wire the execute handler and keep a reference to prevent GC
        eh = _EH()
        args.command.execute.add(eh)
        _h.append(eh)
# --- Core Functions ------------------------------------------------------

def _show_palette():
    """Create or show the calculator palette.
    If the palette already exists but is hidden (user clicked X), make it
    visible again. Only create a new palette if one does not exist at all.
    This avoids the handler accumulation problem caused by delete/recreate."""
    app = adsk.core.Application.get()
    ui  = app.userInterface
    tmp = os.environ.get("TEMP")
    vp  = os.path.join(tmp, "vars.json")

    # Create vars.json if it does not exist yet
    if not os.path.exists(vp):
        open(vp, "w").write("{}")

    # If palette exists but is hidden, just make it visible again
    ex = ui.palettes.itemById(PAL)
    if ex:
        if not ex.isVisible:
            ex.isVisible = True
        return

    # Palette does not exist - create it directly
    base2 = os.path.dirname(os.path.realpath(__file__))
    import time
    url2  = "file:///" + os.path.join(base2, "calculator.html").replace("\\", "/") + "?v=" + str(int(time.time()))
    pal = ui.palettes.add(PAL, "Scientific Calculator", url2, True, True, True, 360, 1100)
    pal.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
    pal.isVisible = True
    hh = _HH(vp)
    pal.incomingFromHTML.add(hh)
    _h.append(hh)
def _poll(ui, rp):
    """Background polling function - runs every 0.4 seconds in a daemon thread.
    Reads the current Fusion active selection, extracts geometry measurements,
    and writes them to sel.json only when the selection has changed.
    The calculator HTML palette reads sel.json periodically via XHR."""
    try:
        result = []
        edge_lengths = []     # Collected for multi-edge sum
        sel_points = []       # Collected points for distance/midpoint/angle

        for i in range(ui.activeSelections.count):
            ent = ui.activeSelections.item(i).entity
            t   = ent.objectType
            try:
                if "BRepEdge" in t:
                    try:
                        import math
                        el = round(ent.length * 10, 4)
                        g = ent.geometry
                        gt = g.objectType
                        if hasattr(g, "radius") and g.radius > 0:
                            rad_mm = round(g.radius * 10, 4)
                            dia_mm = round(g.radius * 20, 4)
                            if "Circle3D" in gt:
                                result.append({"label": "Circle radius",   "value": rad_mm, "unit": "mm"})
                                result.append({"label": "Circle diameter", "value": dia_mm, "unit": "mm"})
                                circ_mm = round(2 * math.pi * g.radius * 10, 4)
                                result.append({"label": "Circumference",   "value": circ_mm, "unit": "mm"})
                            elif "Arc3D" in gt:
                                result.append({"label": "Arc radius",   "value": rad_mm, "unit": "mm"})
                                result.append({"label": "Arc diameter", "value": dia_mm, "unit": "mm"})
                                result.append({"label": "Arc length",   "value": el,     "unit": "mm"})
                                try:
                                    sweep = round(math.degrees(g.endAngle - g.startAngle), 4)
                                    if sweep < 0: sweep += 360
                                    result.append({"label": "Arc sweep", "value": sweep, "unit": "deg"})
                                except: pass
                            elif "Ellipse3D" in gt or "EllipticalArc3D" in gt:
                                result.append({"label": "Ellipse major r", "value": round(g.majorRadius*10,4), "unit": "mm"})
                                result.append({"label": "Ellipse minor r", "value": round(g.minorRadius*10,4), "unit": "mm"})
                                result.append({"label": "Edge length",     "value": el, "unit": "mm"})
                            else:
                                result.append({"label": "Curve radius",   "value": rad_mm, "unit": "mm"})
                                result.append({"label": "Curve diameter", "value": dia_mm, "unit": "mm"})
                                result.append({"label": "Edge length",    "value": el,     "unit": "mm"})
                        else:
                            result.append({"label": "Edge length", "value": el, "unit": "mm"})
                        edge_lengths.append(el)
                    except: pass
                elif "BRepFace" in t:
                    g  = ent.geometry
                    gt = g.objectType
                    if "Cylinder" in gt:
                        import math
                        rad_mm = round(g.radius * 10, 4)
                        dia_mm = round(g.radius * 20, 4)
                        h_mm = None
                        try:
                            ax = g.axis
                            bb = ent.boundingBox
                            dx=bb.maxPoint.x-bb.minPoint.x
                            dy=bb.maxPoint.y-bb.minPoint.y
                            dz=bb.maxPoint.z-bb.minPoint.z
                            h = abs(dx*ax.x+dy*ax.y+dz*ax.z)
                            if h > 0: h_mm = round(h*10, 4)
                        except: pass
                        arc_deg = None
                        try:
                            for loop in ent.loops:
                                for edge in loop.edges:
                                    eg = edge.geometry
                                    egt = eg.objectType
                                    if ("Circle3D" in egt or "Arc3D" in egt) and hasattr(eg,"radius") and eg.radius > 0:
                                        circ = 2*math.pi*eg.radius
                                        frac = edge.length / circ
                                        arc_deg = round(frac * 360, 2)
                                        break
                                if arc_deg is not None: break
                        except: pass
                        if arc_deg is None:
                            try:
                                if h_mm and h_mm > 0:
                                    area = ent.evaluator.area
                                    full = 2*math.pi*g.radius*(h_mm/10)
                                    arc_deg = round((area/full)*360, 2)
                            except: pass
                        is_full = arc_deg is None or arc_deg > 359
                        if is_full:
                            result.append({"label": "Cyl radius",   "value": rad_mm, "unit": "mm"})
                            result.append({"label": "Cyl diameter", "value": dia_mm, "unit": "mm"})
                        else:
                            result.append({"label": "Arc cyl radius",   "value": rad_mm,  "unit": "mm"})
                            result.append({"label": "Arc cyl diameter", "value": dia_mm,  "unit": "mm"})
                            result.append({"label": "Arc cyl angle",   "value": arc_deg, "unit": "deg"})
                        if h_mm:
                            result.append({"label": "Cyl height", "value": h_mm, "unit": "mm"})
                    elif "Sphere" in gt:
                        result.append({"label": "Sphere diameter", "value": round(g.radius * 20, 4), "unit": "mm"})
                    elif "Torus" in gt:
                        result.append({"label": "Torus major radius", "value": round(g.majorRadius * 10, 4), "unit": "mm"})
                        result.append({"label": "Torus minor radius", "value": round(g.minorRadius * 10, 4), "unit": "mm"})
                    elif "Cone" in gt:
                        try:
                            import math
                            ha = round(math.degrees(g.halfAngle), 4)
                            result.append({"label": "Cone half angle", "value": ha, "unit": "deg"})
                            result.append({"label": "Cone full angle", "value": round(ha*2,4), "unit": "deg"})
                            try:
                                ax = g.axis
                                bb = ent.boundingBox
                                dx=bb.maxPoint.x-bb.minPoint.x
                                dy=bb.maxPoint.y-bb.minPoint.y
                                dz=bb.maxPoint.z-bb.minPoint.z
                                h = abs(dx*ax.x+dy*ax.y+dz*ax.z)
                                result.append({"label": "Cone height", "value": round(h*10,4), "unit": "mm"})
                            except: pass
                        except: pass
                    elif "Plane" in gt:
                        try:
                            import math
                            edge_lens = []
                            for edge in ent.edges:
                                try:
                                    el = round(edge.length * 10, 4)
                                    if el > 0.001:
                                        edge_lens.append(el)
                                except: pass
                            if edge_lens:
                                edge_lens.sort(reverse=True)
                                unique = []
                                for el in edge_lens:
                                    if not unique or abs(el - unique[-1]) / max(unique[-1], 0.001) > 0.001:
                                        unique.append(el)
                                labels = ["Face length", "Face width", "Face depth"]
                                for ix, v in enumerate(unique[:3]):
                                    result.append({"label": labels[ix], "value": v, "unit": "mm"})
                        except: pass
                    try:
                        perim = round(sum(e.length*10 for e in ent.edges), 4)
                        if perim > 0:
                            result.append({"label": "Face perimeter", "value": perim, "unit": "mm"})
                    except: pass
                    try:
                        result.append({"label": "Face area", "value": round(ent.evaluator.area * 100, 4), "unit": "mm2"})
                    except:
                        pass
                elif "BRepBody" in t:
                    bb = ent.boundingBox
                    for axis, key in [("X", "x"), ("Y", "y"), ("Z", "z")]:
                        val = round((getattr(bb.maxPoint, key) - getattr(bb.minPoint, key)) * 10, 4)
                        result.append({"label": _safe(ent.name + " " + axis), "value": val, "unit": "mm"})
                    try:
                        pp = ent.getPhysicalProperties(adsk.fusion.CalculationAccuracy.LowCalculationAccuracy)
                        if pp:
                            if pp.volume is not None:
                                result.append({"label": _safe(ent.name+" vol"), "value": round(pp.volume*1000,4), "unit": "mm3"})
                            if pp.area is not None:
                                result.append({"label": _safe(ent.name+" surf area"), "value": round(pp.area*100,4), "unit": "mm2"})
                            if pp.mass is not None and pp.mass > 0:
                                result.append({"label": _safe(ent.name+" mass"), "value": round(pp.mass*1000,4), "unit": "g"})
                            com = pp.centerOfMass
                            result.append({"label": _safe(ent.name+" CoM X"), "value": round(com.x*10,4), "unit": "mm"})
                            result.append({"label": _safe(ent.name+" CoM Y"), "value": round(com.y*10,4), "unit": "mm"})
                            result.append({"label": _safe(ent.name+" CoM Z"), "value": round(com.z*10,4), "unit": "mm"})
                    except: pass

                elif "SketchLine" in t:
                    try:
                        el = round(ent.length * 10, 4)
                        result.append({"label": "Line length", "value": el, "unit": "mm"})
                        edge_lengths.append(el)
                    except: pass

                elif "SketchArc" in t or "SketchCircle" in t:
                    try:
                        import math
                        try:
                            rad = ent.radius
                        except:
                            rad = ent.geometry.radius
                        rad_mm = round(rad * 10, 4)
                        dia_mm = round(rad * 20, 4)
                        result.append({"label": "Radius",   "value": rad_mm, "unit": "mm"})
                        result.append({"label": "Diameter",  "value": dia_mm, "unit": "mm"})
                        try:
                            arc_len = ent.length
                        except:
                            arc_len = rad * 2 * math.pi
                        circ    = 2 * math.pi * rad
                        is_full = (circ > 0) and (arc_len / circ > 0.9999)
                        arc_mm  = round(arc_len * 10, 4)
                        if is_full:
                            result.append({"label": "Circumference", "value": arc_mm, "unit": "mm"})
                            edge_lengths.append(arc_mm)
                        else:
                            result.append({"label": "Arc length", "value": arc_mm, "unit": "mm"})
                            edge_lengths.append(arc_mm)
                            try:
                                g = ent.geometry
                                sa = g.startAngle; ea = g.endAngle
                                sweep = ea - sa
                                if sweep <= 0: sweep += 2 * math.pi
                                result.append({"label": "Arc sweep", "value": round(math.degrees(sweep), 4), "unit": "deg"})
                            except: pass
                    except: pass

                elif "SketchFittedSpline" in t or "SketchSpline" in t:
                    try:
                        el = round(ent.evaluator.length * 10, 4)
                        result.append({"label": "Spline length", "value": el, "unit": "mm"})
                        edge_lengths.append(el)
                    except:
                        try:
                            el = round(ent.length * 10, 4)
                            result.append({"label": "Spline length", "value": el, "unit": "mm"})
                            edge_lengths.append(el)
                        except: pass
                    try:
                        sp = ent.startSketchPoint.worldGeometry
                        result.append({"label": "Spline start X", "value": round(sp.x*10,4), "unit": "mm"})
                        result.append({"label": "Spline start Y", "value": round(sp.y*10,4), "unit": "mm"})
                        result.append({"label": "Spline start Z", "value": round(sp.z*10,4), "unit": "mm"})
                    except: pass
                    try:
                        ep = ent.endSketchPoint.worldGeometry
                        result.append({"label": "Spline end X", "value": round(ep.x*10,4), "unit": "mm"})
                        result.append({"label": "Spline end Y", "value": round(ep.y*10,4), "unit": "mm"})
                        result.append({"label": "Spline end Z", "value": round(ep.z*10,4), "unit": "mm"})
                    except: pass
                    try:
                        fp_count = ent.fitPoints.count
                        result.append({"label": "Spline fit points", "value": fp_count, "unit": ""})
                    except: pass
                elif "SketchConicCurve" in t:
                    try:
                        el = round(ent.evaluator.length * 10, 4)
                        result.append({"label": "Conic length", "value": el, "unit": "mm"})
                        edge_lengths.append(el)
                    except: pass
                    try:
                        result.append({"label": "Conic rho", "value": round(ent.rhoValue, 6), "unit": ""})
                    except: pass
                    try:
                        sp = ent.startSketchPoint.worldGeometry
                        result.append({"label": "Conic start X", "value": round(sp.x*10,4), "unit": "mm"})
                        result.append({"label": "Conic start Y", "value": round(sp.y*10,4), "unit": "mm"})
                        result.append({"label": "Conic start Z", "value": round(sp.z*10,4), "unit": "mm"})
                    except: pass
                    try:
                        ep = ent.endSketchPoint.worldGeometry
                        result.append({"label": "Conic end X", "value": round(ep.x*10,4), "unit": "mm"})
                        result.append({"label": "Conic end Y", "value": round(ep.y*10,4), "unit": "mm"})
                        result.append({"label": "Conic end Z", "value": round(ep.z*10,4), "unit": "mm"})
                    except: pass
                    try:
                        ap = ent.apexSketchPoint.worldGeometry
                        result.append({"label": "Conic apex X", "value": round(ap.x*10,4), "unit": "mm"})
                        result.append({"label": "Conic apex Y", "value": round(ap.y*10,4), "unit": "mm"})
                        result.append({"label": "Conic apex Z", "value": round(ap.z*10,4), "unit": "mm"})
                    except: pass

                elif "BRepVertex" in t:
                    try:
                        g = ent.geometry
                        result.append({"label": "Vertex X", "value": round(g.x*10,4), "unit": "mm"})
                        result.append({"label": "Vertex Y", "value": round(g.y*10,4), "unit": "mm"})
                        result.append({"label": "Vertex Z", "value": round(g.z*10,4), "unit": "mm"})
                        sel_points.append(g)
                    except: pass

                elif "SketchPoint" in t:
                    try:
                        sg = ent.geometry
                        wg = ent.worldGeometry
                        result.append({"label": "Point X (sketch)", "value": round(sg.x*10,4), "unit": "mm"})
                        result.append({"label": "Point Y (sketch)", "value": round(sg.y*10,4), "unit": "mm"})
                        result.append({"label": "Point X (world)",  "value": round(wg.x*10,4), "unit": "mm"})
                        result.append({"label": "Point Y (world)",  "value": round(wg.y*10,4), "unit": "mm"})
                        result.append({"label": "Point Z (world)",  "value": round(wg.z*10,4), "unit": "mm"})
                        sel_points.append(wg)
                    except: pass

            except:
                pass

        if len(edge_lengths) > 1:
            result.append({"label": "Sum of lengths", "value": round(sum(edge_lengths), 4), "unit": "mm"})
        if len(sel_points) == 2:
            import math
            p1, p2 = sel_points[0], sel_points[1]
            dx = (p2.x-p1.x)*10; dy = (p2.y-p1.y)*10; dz = (p2.z-p1.z)*10
            dist = round(math.sqrt(dx*dx+dy*dy+dz*dz), 4)
            result.append({"label": "Distance", "value": dist, "unit": "mm"})
            result.append({"label": "Mid X", "value": round((p1.x+p2.x)*5, 4), "unit": "mm"})
            result.append({"label": "Mid Y", "value": round((p1.y+p2.y)*5, 4), "unit": "mm"})
            result.append({"label": "Mid Z", "value": round((p1.z+p2.z)*5, 4), "unit": "mm"})
        if ui.activeSelections.count == 2:
            try:
                import math
                e1 = ui.activeSelections.item(0).entity
                e2 = ui.activeSelections.item(1).entity
                if "BRepEdge" in e1.objectType and "BRepEdge" in e2.objectType:
                    ev1 = e1.evaluator; ev2 = e2.evaluator
                    params1 = ev1.getParameterExtents(); params2 = ev2.getParameterExtents()
                    t1 = ev1.getFirstDerivative((params1[1]+params1[2])*0.5)[1]
                    t2 = ev2.getFirstDerivative((params2[1]+params2[2])*0.5)[1]
                    dot = t1.x*t2.x + t1.y*t2.y + t1.z*t2.z
                    m1 = math.sqrt(t1.x**2+t1.y**2+t1.z**2)
                    m2 = math.sqrt(t2.x**2+t2.y**2+t2.z**2)
                    if m1>0 and m2>0:
                        cos_a = max(-1.0, min(1.0, dot/(m1*m2)))
                        ang_deg = round(math.degrees(math.acos(cos_a)), 4)
                        if ang_deg > 90: ang_deg = round(180-ang_deg, 4)
                        result.append({"label": "Edge angle", "value": ang_deg, "unit": "deg"})
            except: pass
        if ui.activeSelections.count == 2:
            try:
                import math
                f1 = ui.activeSelections.item(0).entity
                f2 = ui.activeSelections.item(1).entity
                if "BRepFace" in f1.objectType and "BRepFace" in f2.objectType:
                    def _get_normal(face):
                        bb = face.boundingBox
                        cx = (bb.maxPoint.x + bb.minPoint.x) / 2
                        cy = (bb.maxPoint.y + bb.minPoint.y) / 2
                        cz = (bb.maxPoint.z + bb.minPoint.z) / 2
                        pt = adsk.core.Point3D.create(cx, cy, cz)
                        _, param = face.evaluator.getParameterAtPoint(pt)
                        _, nrm = face.evaluator.getNormalAtParameter(param)
                        return nrm
                    def _get_centre(face):
                        bb = face.boundingBox
                        return adsk.core.Point3D.create(
                            (bb.maxPoint.x + bb.minPoint.x) / 2,
                            (bb.maxPoint.y + bb.minPoint.y) / 2,
                            (bb.maxPoint.z + bb.minPoint.z) / 2)
                    n1 = _get_normal(f1)
                    n2 = _get_normal(f2)
                    dot = n1.x*n2.x + n1.y*n2.y + n1.z*n2.z
                    dot = max(-1.0, min(1.0, dot))
                    if abs(abs(dot) - 1.0) < 0.001:
                        c1 = _get_centre(f1)
                        c2 = _get_centre(f2)
                        dx = c2.x - c1.x; dy = c2.y - c1.y; dz = c2.z - c1.z
                        dist = abs(dx*n1.x + dy*n1.y + dz*n1.z)
                        result.append({"label": "Face distance", "value": round(dist * 10, 4), "unit": "mm"})
                    else:
                        ang = round(math.degrees(math.acos(dot)), 4)
                        result.append({"label": "Face normal angle", "value": ang, "unit": "deg"})
                        result.append({"label": "Dihedral angle", "value": round(180 - ang, 4), "unit": "deg"})
            except: pass

        key = json.dumps(result)
        if key != _prev[0]:
            _prev[0] = key
            _aw(rp, key)

    except:
        pass

    _timer[0] = threading.Timer(0.4, _poll, args=[ui, rp])
    _timer[0].daemon = True
    _timer[0].start()
# --- Add-In Entry Points -------------------------------------------------

def run(_context):
    """Called by Fusion when the add-in is loaded (at startup or manually).
    Registers the toolbar button, starts the selection poller,
    and opens the calculator palette."""
    app = adsk.core.Application.get()
    ui  = app.userInterface
    tmp = os.environ.get("TEMP")
    rp  = os.path.join(tmp, "sel.json")

    _aw(rp, "[]")

    base     = os.path.dirname(os.path.realpath(__file__))
    icon_dir = os.path.join(base, "icons")
    os.makedirs(icon_dir, exist_ok=True)
    for sz in [16, 32, 40, 64]:
        open(os.path.join(icon_dir, "%dx%d.png" % (sz, sz)), "wb").write(_mkpng(sz, 56, 89, 152))

    ex = ui.commandDefinitions.itemById(CMD)
    if ex:
        ex.deleteMe()

    cmd = ui.commandDefinitions.addButtonDefinition(
        CMD, "Scientific Calculator", "Open Scientific Calculator", icon_dir
    )

    cch = _CCH()
    cmd.commandCreated.add(cch)
    _h.append(cch)

    for i in range(ui.workspaces.count):
        try:
            ws    = ui.workspaces.item(i)
            panel = ws.toolbarPanels.itemById("InspectPanel")
            if panel and not panel.controls.itemById(CMD):
                ctrl = panel.controls.addCommand(cmd)
                if ctrl:
                    ctrl.isPromoted = True
        except:
            pass

    if _timer[0]:
        _timer[0].cancel()
    _timer[0] = threading.Timer(0.4, _poll, args=[ui, rp])
    _timer[0].daemon = True
    _timer[0].start()

    _show_palette()

def stop(_context):
    """Called by Fusion when the add-in is unloaded.
    Cancels the polling timer and removes all UI elements we created."""
    try:
        if _timer[0]:
            _timer[0].cancel()

        ui = adsk.core.Application.get().userInterface

        for i in range(ui.workspaces.count):
            try:
                ws    = ui.workspaces.item(i)
                panel = ws.toolbarPanels.itemById("InspectPanel")
                if panel:
                    ctrl = panel.controls.itemById(CMD)
                    if ctrl:
                        ctrl.deleteMe()
            except:
                pass

        ex = ui.commandDefinitions.itemById(CMD)
        if ex:
            ex.deleteMe()

        pal = ui.palettes.itemById(PAL)
        if pal:
            pal.deleteMe()

    except:
        pass

    _h.clear()

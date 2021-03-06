init python:

    config.window_title = "Spline Editor"
    
    theme.roundrect()

    style.window.background = None
    
    _game_menu_screen = None

    class Point(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    import pygame
    import os
    
    HANDLE_SIZE = 9
    DOT_SIZE = 3

    # The size of the viewable area of the screen.
    X = 150
    Y = 112
    W = 500
    H = 375
    
    class SplineEditor(renpy.Displayable):

        def __init__(self):
            super(SplineEditor, self).__init__()

            self.mode = "addmove"
            
            self.lead_handle = [ ]
            self.points = [ ]
            self.trail_handle = [ ]

            self.handle = Image("handle.png")
            self.point = Image("bullet.png")
            self.dot = Image("dot.png")
            
            self.dragging = None
            self.reflect = None
            self.reflected = None
            self.relative_drag = [ ]

            self.spline_dots = [ ]
            self.spline_points = [ ]

            self.delay = 3.0
            self.closed = False
            
        def render(self, width, height, st, at):

            rv = renpy.Render(width, height)
            
            handle = renpy.render(self.handle, width, height, st, at)
            point = renpy.render(self.point, width, height, st, at)
            dot = renpy.render(self.dot, width, height, st, at)

            for i in self.points:
                rv.blit(point, (i.x - HANDLE_SIZE / 2, i.y - HANDLE_SIZE / 2))

            for i in self.lead_handle:
                rv.blit(handle, (i.x - HANDLE_SIZE / 2, i.y - HANDLE_SIZE / 2))

            for i in self.trail_handle:
                rv.blit(handle, (i.x - HANDLE_SIZE / 2, i.y - HANDLE_SIZE / 2))

            for i in self.spline_dots:
                rv.blit(dot, i)
                
            # This isn't supported, as it uses some internals that might change.
            # Don't try this at home, kids.
            surf = pygame.Surface((width, height), 0, renpy.game.interface.display.sample_surface)

            for (a, p, b) in zip(self.lead_handle, self.points, self.trail_handle):
                pygame.draw.aaline(surf, (0, 0, 255, 64), (a.x, a.y), (p.x, p.y))
                pygame.draw.aaline(surf, (0, 0, 255, 64), (b.x, b.y), (p.x, p.y))
            
            rv.blit(surf, (0, 0))


            delay = renpy.render(Text("%.1f" % self.delay, color="#000"), width, height, st, at)
            rv.blit(delay, (693, 547))
            
            return rv
                

        def event(self, ev, x, y, st):

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.mouse1down(x, y)

            if ev.type == pygame.MOUSEMOTION or (ev.type == pygame.MOUSEBUTTONUP and ev.button == 1):
                self.mousemotion(x, y)
                
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.mouse1up(x, y)

            if ev.type == pygame.KEYDOWN:
                self.keydown(ev.key, ev.unicode)


                
        def mouse1down(self, x, y):

            if self.mode == "addmove":

                # True if we're close enough to the handle to drag it.
                def near(p):
                    if abs(p.x - x) <= HANDLE_SIZE / 2 and abs(p.y - y) <= HANDLE_SIZE / 2:
                        return True
                    else:
                        return False

                point = None
                relative = [ ]
                
                for p, p1, p2 in zip(self.points, self.lead_handle, self.trail_handle):
                    if near(p):
                        point = p
                        relative = [
                            (p1.x - p.x, p1.y - p.y, p1),
                            (p2.x - p.x, p2.y - p.y, p2),
                            ]
                        
                for p in self.lead_handle:
                    if near(p):
                        point = p
                        relative = [ ]
                        
                for p in self.trail_handle:
                    if near(p):
                        point = p
                        relative = [ ]
                        
                if point:
                    self.mode = "drag"
                    self.dragging = point
                    self.relative_drag = relative
                    return 
                
                self.dragging = Point(x, y)
                self.reflect = Point(x, y)
                self.reflected = Point(x, y)

                self.points.append(self.reflect)
                self.lead_handle.append(self.reflected)
                self.trail_handle.append(self.dragging)

                self.mode = "mirrordrag"
                self.recompute_spline()
                renpy.redraw(self, 0)

        def mousemotion(self, x, y):

            if self.mode == "mirrordrag":

                self.dragging.x = x
                self.dragging.y = y

                self.reflected.x = 2 * self.reflect.x - x
                self.reflected.y = 2 * self.reflect.y - y

                self.recompute_spline()                
                renpy.redraw(self, 0)

            if self.mode == "drag":
                self.dragging.x = x
                self.dragging.y = y

                for (xo, yo, p) in self.relative_drag:
                    p.x = xo + x
                    p.y = yo + y
                
                self.recompute_spline()                
                renpy.redraw(self, 0)
                

        def mouse1up(self, x, y):
            if self.mode == "mirrordrag":
                self.mode = "addmove"
                
            if self.mode == "drag":
                self.mode = "addmove"

        def keydown(self, key, unicode):
            if key == pygame.K_DELETE or key == pygame.K_BACKSPACE:
                if self.points:
                    self.points.pop()
                    self.lead_handle.pop()
                    self.trail_handle.pop()

            elif unicode == "p":
                renpy.jump("preview")
                    
            elif unicode == "+":
                self.delay += .1

            elif unicode == "-":
                self.delay -= .1
                if self.delay < .1:
                    self.delay = .1

            elif unicode == "c":
                self.closed = not self.closed

            elif unicode == "n":
                renpy.jump("start")

            elif unicode == "w":
                renpy.jump("write")
                
            self.recompute_spline()
            renpy.redraw(self, 0)
            
                
                
        def recompute_spline(self):
            self.spline_dots = [ ]

            spline_points = [ ]
            self.spline_points = spline_points

            if len(self.points) < 2:
                return

            spline_points.append(((self.points[0].x, self.points[0].y),))

            for i in range(0, len(self.points) - 1):
                spline_points.append((
                        (self.points[i+1].x,
                         self.points[i+1].y),
                        (self.trail_handle[i].x,
                         self.trail_handle[i].y),
                        (self.lead_handle[i+1].x,
                         self.lead_handle[i+1].y),
                        ))

            if self.closed:
                spline_points.append((
                        (self.points[0].x,
                         self.points[0].y),
                        (self.trail_handle[-1].x,
                         self.trail_handle[-1].y),
                        (self.lead_handle[0].x,
                         self.lead_handle[0].y),
                        ))
                
            pi = _SplineInterpolator(spline_points)

            if self.closed:
                numdots = len(self.points) * 15
            else:
                numdots = (len(self.points) - 1) * 15
                
            for j in range(0, numdots + 1):
                t = 1.0 * j / numdots

                x, y, xo, yo = pi(t, (800, 600, DOT_SIZE, DOT_SIZE))
                self.spline_dots.append((x, y))


        def relative_spline(self):
            def make_relative(t):
                x, y = t
                return (1.0 * (x - X) / W, 1.0 * (y - Y) / H)
            
            return list(tuple(make_relative(i) for i in j) for j in self.spline_points)

    # Nicely formats nested tuples and floats.
    def format(v):
        if isinstance(v, tuple):
            return "(" + ", ".join(format(i) for i in v) + ",)"
        else:
            return "%.3f" % v
            
            
    
label confirm_quit:
    $ renpy.quit()
    
label main_menu:
    return

label start:

    python:
        se = SplineEditor()

label edit:
    scene expression "background.jpg"

    python:
        ui.add(se)
        ui.interact()

label preview:

    scene black

    if not se.spline_points:
        "A spline must have at least two points in it."
    else:
        show expression "smile.png" at SplineMotion(se.relative_spline(), se.delay, repeat=True)
        "Previewing path. Click to continue."

    jump edit
    
label write:

    scene black
    
    if not se.spline_points:
        "A spline must have at least two points in it."
        jump edit

    python hide:
        f = file("splinedata.rpy", "w")
        f.write("init python:\n")
        f.write("    spline = SplineMotion([\n")
        for t in se.relative_spline():
            f.write("        %s,\n" % format(t))
        f.write("        ], %.1f, anchors=(0.5, 0.5), repeat=False)\n" % se.delay)
        f.close()

        print file("splinedata.rpy").read()
        
        renpy.launch_editor([ "splinedata.rpy" ], 1, transient=1)
        
    "Information about this spline was written to splinedata.rpy.\nClick to continue."

    jump edit
        
        
        
    
    

    

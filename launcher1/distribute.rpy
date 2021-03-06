# This file contains the code needed to build a Ren'Py distribution.

init python:
    import zipfile
    import tarfile
    import os
    import os.path
    import time
    import sys
    import zlib

    import pefile
    
    # Returns true if a file or directory should not be included in
    # the distribution
    
    ignored_files = ("thumbs.db",
                     "launcherinfo.py",
                     "traceback.txt",
                     "errors.txt",
                     "icon.ico",
                     "icon.icns"
                     )


    root_ignored_files = (
        "common",
        "renpy",
        "renpy.code",
        "python23.dll",
        "python24.dll",
        "python25.dll",
        "msvcr71.dll",                     
        "lib",
        "iliad-icon.png",
        "manifest.xml"
        )
    
    def ignored(fn, dir, dest, root):
        if fn[0] == ".":
            return True

        for i in store.ignore_extensions:
            if fn.endswith(i):
                return True

        if fn.lower() in ignored_files:
            return True

        if fn == "saves":
            return True

        if fn == "archived":
            return True

        if root and dir == dest:
            if fn.endswith(".py") or fn.endswith(".sh") or fn.endswith(".app"):
                return True

            if fn in root_ignored_files:
                return True
            
        return False

    def tree(src, dest,
             exclude_suffix=[ ".pyc", "~", ".bak" ],
             exclude_prefix=[ ".", '#' ],
             exclude=ignored_files,
             exclude_func=ignored,
             root=False,
             ):

        # Get rid of trailing slashes.
        if src[-1] == "/":
            src = src[:-1]

        if dest and dest[-1] == "/":
            dest = dest[:-1]

        # What should we include?
        def include(fn, destdir, dest):
            for i in exclude_suffix:
                if fn.endswith(i):
                    return False

            for i in exclude_prefix:
                if fn.startswith(i):
                    return False

            for i in exclude:
                if i == fn.lower():
                    return False

            if exclude_func and exclude_func(fn, destdir, dest, root):
                return False

            return True


        rv = [ ]

        # Walk the tree, including what is necessary.
        for srcdir, dirs, files in os.walk(src):

            if dest:
                destdir = dest + srcdir[len(src):]
            else:
                destdir = srcdir[len(src) + 1:]

            if destdir:
                rv.append((srcdir, destdir))

            for fn in files:

                if not include(fn, destdir, dest):
                    continue

                sfn = srcdir + "/" + fn

                if destdir:
                    dfn = destdir + "/" + fn
                else:
                    dfn = fn

                dfn = dfn.replace("\\", "/")
                    
                rv.append((sfn, dfn))

            dirs[:] = [ i for i in dirs if include(i, destdir, dest) ]

        return rv

        
label distribute:

    python hide:
        zlib.Z_DEFAULT_COMPRESSION = 9

        store.progress_time = 0

        def progress(tit, n, m, time=time):
            
            if time.time() < store.progress_time + .1:
                return

            title(tit)

            mid(message)
            ui.bar(m, n, xmaximum=200, xalign=0.5)
            ui.close()

            ui.pausebehavior(0)
            interact()
            
        # Check to see which platforms we can build on.
        if os.path.exists(config.renpy_base + "/renpy.exe"):
            windows = True
        else:
            windows = False

        if os.path.exists(config.renpy_base + "/lib/linux-x86"):
            linux = True
        else:
            linux = False

        if os.path.exists(config.renpy_base + "/lib/linux-iliad"):
            iliad = True
        else:
            iliad = False

        if os.path.exists(config.renpy_base + "/renpy.app"):
            mac = True
        else:
            mac = False
            
        if not (windows or mac or linux or iliad):
            store.error(u"Can't Distribute", u"Ren'Py is missing files required for distribution. Please download the full package from {a=http://www.renpy.org/}www.renpy.org{/a}.", "tools_menu")
        
        lint()

        store.message = ""

        title(_(u"Building Distributions"))

        mid()
        text(u"I've just performed a lint on your project. If it contains errors, you should say no and fix them.\nCheck {a=http://www.renpy.org/wiki/renpy/Download_Ren'Py}www.renpy.org{/a} to see if updates or fixes are available.\n\nDo you want to continue?")
        ui.close()

        bottom()
        button(u"Yes", clicked=ui.returns(True))
        button(u"No", clicked=ui.returns(False))
        ui.close()

        if not interact():
            renpy.jump("tools")


        # if not windows or not mac or not linux:
        #    store.message = "The full version of Ren'Py can build for Windows, Mac, and Linux. Download it from www.renpy.org."
            
        title(u"Building Distributions")

        mid()
        text(u"Distributions will be built for the following platforms:")

        spacer()

        if windows:
            text(u"Windows 2000+", style='launcher_input')

        if linux:
            text(u"Linux x86", style='launcher_input')

        if iliad:
            text(u"iLiad", style='launcher_input')
                        
        if mac:
            text(u"Mac OS X 10.4+", style='launcher_input')

        spacer()


        # TODO: If missing platforms, prompt for a DL.

        text(u"Is this okay?")
        ui.close()

        bottom()
        button(u"Yes", clicked=ui.returns(True))
        button(u"No", clicked=ui.returns(False))
        ui.close()

        if not interact():
            renpy.jump("tools")

        default_name = project.info.get('distribution_base', project.name)

        name = prompt(u"Building Distributions",
                      u"Please enter a base name for the directories making up this distribution.",
                      "tools",
                      default_name,
                      u"This usually should include a name and version number, like 'moonlight_walks-1.0'.")

        name = name.strip()

        if not name:
            store.error(u"Error", u"The distribution name should not be empty.", "tools_menu")

        try:
            name = name.encode("ascii")
        except:
            store.error(u"Error", u"Distribution names must be ASCII. This is because archive file formats do not support non-ASCII characters in a uniform way.", "tools_menu")

        project.info['distribution_base'] = name

        ignore_extensions = project.info.get('ignore_extensions', "~ .bak")
        ignore_extensions = prompt(u"Building Distributions", u"Please enter a space separated list of the file extensions you do not want included in the distribution.", "tools", ignore_extensions)
        store.ignore_extensions = [ i.strip() for i in ignore_extensions.strip().split() ]
        project.info['ignore_extensions'] = ignore_extensions    

        project.save()
        
        # Figure out the files that will make up the distribution.

        multi = [ ]

        # This finds the files and directories in the tree, and includes
        # them in the result.

                
        # renpy and common directories.
        multi.extend(tree(config.renpy_base + "/renpy", "renpy"))
        multi.append((config.renpy_base + "/LICENSE.txt", "renpy/LICENSE.txt"))
        multi.extend(tree(config.commondir, "common"))
        
        # Include the project.
        multi.extend(tree(project.path, '',
                          exclude_suffix = [ ],
                          exclude_prefix = [ ],
                          exclude=[ ],
                          root=True))
        
        shortgamedir = project.gamedir[len(project.path)+1:]


        def add_script_version(fn, multi=multi, shortgamedir=shortgamedir):

            for a, b in multi:
                if b == shortgamedir + "/" + fn:
                    return

            for i in store.ignore_extensions:
                if fn.endswith(i):
                    return 

            multi.append((config.gamedir + "/" + fn, shortgamedir + "/" + fn))

        add_script_version("script_version.rpy")
        add_script_version("script_version.rpyc")
            
        # renpy.py
        multi.append((config.renpy_base + "/renpy.py",
                      project.name + ".py"))

        # Windows Zip
        if windows:
            win_files = [
                ( config.renpy_base + "/renpy.exe", project.name + ".exe"),
                ( config.renpy_base + "/renpy.code", "renpy.code" ),
                ( config.renpy_base + "/python25.dll", "python25.dll" ),
                ( config.renpy_base + "/msvcr71.dll", "msvcr71.dll" ),
                ]

            win_data = { }
            if os.path.exists(project.path + "/icon.ico"):
                win_data[project.name + ".exe"] = pefile.change_icons(
                    config.renpy_base + "/renpy.exe",
                    project.path + "/icon.ico",
                    )
            
            zf = zipfile.ZipFile(name + ".zip", "w", zipfile.ZIP_DEFLATED)

            progress_len = len(multi) + len(win_files)
            store.message = u"Be sure to announce your project at the Lemma Soft Forums."
                               
            for i, (fn, an) in enumerate(multi + win_files):
                progress(u"Building Windows", i, progress_len)

                if os.path.isdir(fn):
                    continue
                
                zi = zipfile.ZipInfo(name + "/" + an)

                s = os.stat(fn)
                zi.date_time = time.gmtime(s.st_mtime)[:6]
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.create_system = 3

                zi.external_attr = long(0100666) << 16 
                data = file(fn, "rb").read()

                data = win_data.get(an, data)
                
                zf.writestr(zi, data)


            zf.close()


        # Linux Tar Bz2
        if linux:

            linux_files = [
                (config.renpy_base + "/lib/linux-x86", "lib/linux-x86"),
                (config.renpy_base + "/renpy.sh", project.name + ".sh"),
                (config.renpy_base + "/lib/python", "lib/python"),
                ]
                

            linux_files.extend(tree(config.renpy_base + "/lib/linux-x86", "lib/linux-x86"))

            tf = tarfile.open(name + "-linux-x86.tar.bz2", "w:bz2")
            tf.dereference = True

            progress_len = len(multi) + len(linux_files)
            store.message = u"If appropriate, please submit your game to www.renai.us."

            for j, i in enumerate(multi + linux_files):

                progress(u"Building Linux", j, progress_len)

                fn, an = i

                info = tf.gettarinfo(fn, name + "-linux-x86/" + an)

                if info.isdir():
                    perms = 0777
                elif info.name.endswith(".sh"):
                    perms = 0777
                elif info.name.endswith(".so"):
                    perms = 0777
                elif info.name.endswith("python"):
                    perms = 0777
                elif info.name.endswith("python.real"):
                    perms = 0777
                else:
                    perms = 0666

                info.mode = perms
                info.uid = 1000
                info.gid = 1000
                info.uname = "renpy"
                info.gname = "renpy"

                if info.isreg():
                    tf.addfile(info, file(fn, "rb"))
                else:
                    tf.addfile(info)

            tf.close()


        # iLiad Tar Bz2
        if iliad:

            iliad_files = [
                (config.renpy_base + "/lib", "lib"),
                (config.renpy_base + "/renpy-iliad.sh", project.name + ".sh"),
                (config.renpy_base + "/lib/python", "lib/python"),
                (config.renpy_base + "/manifest.xml", "manifest.xml"),
                (config.renpy_base + "/iliad-icon.png", "iliad-icon.png"),
                ]
                
            iliad_files.extend(tree(config.renpy_base + "/lib/linux-iliad", "lib/linux-iliad"))

            iliad_data = { }

            manifest = file(config.renpy_base + "/manifest.xml", "r").read()
            manifest = manifest.replace("GAMENAME", project.name)
            iliad_data["manifest.xml"] = manifest
            
            zf = zipfile.ZipFile(name + "-iLiad.zip", "w", zipfile.ZIP_DEFLATED)

            progress_len = len(multi) + len(iliad_files)
            store.message = u"We thank Hixbooks for sponsoring iLiad support."

            for i, (fn, an) in enumerate(multi + iliad_files):

                progress(u"Building iLiad", i, progress_len)

                if os.path.isdir(fn):
                    continue
                
                zi = zipfile.ZipInfo(project.name + "/" + an)
                
                s = os.stat(fn)
                zi.date_time = time.gmtime(s.st_mtime)[:6]
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.create_system = 3

                for ext in [ ".sh", ".so", "python", "python.real" ]:
                    if fn.endswith(ext):
                        zi.external_attr = long(0100777) << 16 
                        data = file(fn, "rb").read()
                        break
                else:
                    zi.external_attr = long(0100666) << 16 
                    data = file(fn, "rb").read()

                data = iliad_data.get(an, data)                    
                zf.writestr(zi, data)

            zf.close()

        if mac:

            mac_files = tree(config.renpy_base + "/renpy.app",
                             project.name + ".app")

            mac_files = [ (fn, an.replace("Ren'Py Launcher", project.name)) for (fn, an) in mac_files ]

            # Data replacement for macintosh.
            mac_data = { }
            
            quoted_name = project.name.replace("&", "&amp;").replace("<", "&lt;")                                               
            info_plist = file(config.renpy_base + "/renpy.app/Contents/Info.plist", "rb").read().replace("Ren'Py Launcher", quoted_name)
            mac_data[project.name + ".app/Contents/Info.plist"] = info_plist

            quoted_name = project.name.replace("\"", "\\\"")
            launcher_py = file(config.renpy_base + "/renpy.app/Contents/Resources/launcher.py", "rb").read().replace("Ren'Py Launcher", quoted_name)
            mac_data[project.name + ".app/Contents/Resources/launcher.py"] = launcher_py

            if os.path.exists(project.path + "/icon.icns"):
                icon_data = file(project.path + "/icon.icns", "rb").read()
                mac_data[project.name + ".app/Contents/Resources/launcher.icns"] = icon_data
            
            zf = zipfile.ZipFile(name + "-mac.zip", "w", zipfile.ZIP_DEFLATED)

            progress_len = len(multi) + len(mac_files)
            store.message = u"Thank you for choosing Ren'Py."

            for i, (fn, an) in enumerate(multi + mac_files):

                progress(u"Building Mac OS X", i, progress_len)

                if os.path.isdir(fn):
                    continue
                
                zi = zipfile.ZipInfo(name + "-mac/" + an)
                
                s = os.stat(fn)
                zi.date_time = time.gmtime(s.st_mtime)[:6]
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.create_system = 3

                if os.path.dirname(fn).endswith("MacOS") or fn.endswith(".so") or fn.endswith(".dylib"):
                    zi.external_attr = long(0100777) << 16 
                    data = file(fn, "rb").read()
                else:
                    zi.external_attr = long(0100666) << 16 
                    data = file(fn, "rb").read()

                data = mac_data.get(an, data)                    
                zf.writestr(zi, data)

            zf.close()

                
        # Announce Success

        store.message = ""

        title(u"Success")

        mid()
        text(u"The distribution(s) have been built. Be sure to test them before release.")

        spacer()

        if mac:
            text(u"Note that unpacking and repacking Mac zips and Linux tarballs on Windows isn't supported.")

        ui.close()

        bottom()
        button(u"Return", clicked=ui.returns(True))
        ui.close()
        
        interact()

        
    jump tools
               
        

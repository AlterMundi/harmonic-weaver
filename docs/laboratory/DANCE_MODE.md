# Dance view

After setting up the source and sound, press **Bailar** in the toolbar.
The existing camera/video and observed body overlay occupy the viewport; the same
harmonic figure appears in a small window at the lower right. The body remains
fully fitted, including portrait sources, rather than being cropped to fill the screen.
The ordinary large two-viewer layout returns on exit.

The human's click requests browser fullscreen. If unsupported or refused, the
same view fills the current tab and says so. **Volver al set** exits; **Esc** exits
native fullscreen or the full-tab fallback. Focus returns to the launch control.
No fullscreen request is made automatically at startup or after reconnect.

The source element, tracking overlay, single figure canvas and recorder remain
mounted. Entering/leaving does not open/close a camera, resume playback, edit the
preset or stop a recording. The six voices, gain and routing remain selected as
before. Setup controls are hidden only in this presentation. Dance view shows the
existing observed/conditioned skeleton without persisting a change to the preset's
show_skeleton flag. It does not fill missing joints or manufacture movement.
A real connection/camera error remains visible with the exit control.

The corner figure is the existing geometric representation of active oscillators,
not a new audio/physical cymatics measurement or an extra synthesis path. Resizing
uses the existing renderer; no duplicate camera stream or render loop is created.

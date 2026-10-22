# Skill: Whole-die-with-pins image snapshot

Render a PNG that shows the **entire die plus the top-level IO pins**, so a
checker (or human) can see the macro placement *and* which die edges the pins
sit on. This is exactly what the agent flow saves at every stage; use the
standalone tool to capture it on demand from any checkpoint.

## What "whole die with pins" means

The saved area is the **die box**, expanded outward by a small `margin` so the
boundary pins are not clipped, and (if enabled) the pin boxes are redrawn on top
because OpenROAD rasterizes thin pins to near-invisibility at the die zoom.

Settings live in `config.yaml`:

```yaml
image:
  save_width: 1024     # save_image -width (px); height keeps the layout aspect
  margin: 0.03         # fractional pad around die/pins (0.03 = 3% of the larger side)
  pin_overlay: true    # redraw bterm boxes over the PNG so pins stay visible
```

## The code path (flow)

1. `macroflow/recipes.py` `DIE_CORE` + `PIN_COORDS` query the die box and every
   bterm pin box from OpenROAD.
2. `macroflow/context.py` `FlowState.image_area(margin)` unions the die (+ any
   out-of-die pin boxes) and pads by `margin`.
3. `macroflow/openroad.py` `ORSession.save_image()` emits
   `save_image -area {x0 y0 x1 y1} -width 1024 image.png`.
4. If `pin_overlay: true`, `macroflow/context.py` `draw_pin_overlay()` draws the
   pin boxes on top of the OpenROAD PNG.

For **bp_fe** (`DIE_AREA 0 0 800 600`, `margin 0.03`) the area becomes
`-24 -24 824 624`, so the manual OpenROAD command is:

```tcl
save_image -area {-24 -24 824 624} -width 1024 whole_die_with_pins.png
```

`margin` is a fraction of the larger die side: `pad = max(w, h) * margin`,
so `800 * 0.03 = 24`.

## Standalone capture

`skills/skills_Nangate45/macro_pin_side/macro_pin_side.py` uses the same
whole-die-with-pins convention, so use it to capture any checkpoint on demand.
`<design>_raw.png` is the plain whole-die image; `<design>_pin_side.png` adds
the macro pin-side bars:

```bash
python skills/skills_Nangate45/macro_pin_side/macro_pin_side.py \
    --odb <work-dir>/saves_db/floorplan.odb \
    --out-dir work_images --design snapshot
```

## Notes

- ODB mode is preferred: a single `read_db` restores tech + LEF + placement.
- The session runs headless (`QT_QPA_PLATFORM=minimal`); no X server needed.

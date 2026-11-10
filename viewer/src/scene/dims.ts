// Enclosure dimensions (mm). Enclosure frame: X = PCB x, Y = −PCB y (back panel at Y > 0), Z up from the
// bottom face of the tray.
//
// SOURCE OF TRUTH: enclosure/enclosure.py (itself synced with hardware/scripts/gen_pcb.py). Keep both files
// consistent: every `export const NAME = literal` below that has the same name in enclosure.py is checked by
// `npm run assets` (scripts/convert_assets.py, check_dims), which fails if they drift. Keep each of those
// constants a one-line JSON literal so the check can read it.

export const PCB_W = 90.0
export const PCB_D = 62.0
export const PCB_T = 1.6
export const Z_FLOOR = 3.0
export const Z_PCB_BOT = 7.5 // FLOOR + STANDOFF
export const Z_PCB_TOP = 9.1
export const Z_CEIL = 22.1
export const Z_SPLIT = 13.0 // SPLIT_H, tray / lid parting line
export const H_TOTAL = 25.1 // H

export const X0 = -3.5
export const X1 = 93.5
export const Y0 = -66.3
export const Y1 = 4.3

export const Y_BACK_IN = 0.3
export const Y_BACK_OUT = 2.8
export const Y_FRONT_IN = -62.3
export const Y_FRONT_OUT = -64.8
export const PANEL_T = 2.5

export const CENTER = { x: (X0 + X1) / 2, y: (Y0 + Y1) / 2 }
/** Diagonal of the footprint, used to scale the camera views. */
export const SIZE = Math.hypot(X1 - X0, Y1 - Y0)

/** Mounting holes, (x, y) PCB -> (x, −y) enclosure */
export const HOLES: [number, number][] = [[4.0, 4.0], [86.0, 4.0], [3.8, 45.5], [86.2, 45.5]]

/** Rubber feet (Ø10 recesses under the tray, enclosure.py tray(): X0 + 9 / Y0 + 9) */
export const FEET: [number, number][] = [
  [X0 + 9, Y0 + 9],
  [X1 - 9, Y0 + 9],
  [X0 + 9, Y1 - 9],
  [X1 - 9, Y1 - 9],
]
export const FOOT_H = 1.5 // below the enclosure (2 mm foot in a 0.5 mm recess)

// ------------------------------------------------------------------ panel parts (PCB x of the axis)
export const JACK_IN_X = 19.0 // JACKS["IN"]
export const JACK_OUT_X = 40.0 // JACKS["OUT"]
export const DC_X = 57.5
export const LED_X = 86.0
/** 31 / 40 / 50 / 63 / 80 Hz, left to right seen from the front */
export const POT_X = [15.0, 30.0, 45.0, 60.0, 75.0]
export const POT_LABELS = ['31', '40', '50', '63', '80']

// ------------------------------------------------------------------ parts without a KiCad 3D model (enclosure.py)
/** Neutrik NMJ4HCD2: axis above the PCB */
export const JACK_H = 3.53
/** width, depth behind the panel inner face, height above the PCB */
export const JACK_BODY = [18.2, 23.53, 11.67]
/** threaded nose in front of the panel inner face (enclosure.py envelopes(): Ø11, 5.8 long) */
export const JACK_NOSE = { d: 11.0, len: 5.8 }
/** Alps RK09L: axis above the PCB */
export const POT_H = 3.5
/** width over the lugs, depth behind the bushing shoulder, top above the PCB */
export const POT_BODY = [12.1, 7.45, 8.35]
/** M9 bushing (enclosure.py envelopes(): Ø9, 5 long from the shoulder = panel inner face) */
export const POT_BUSHING = { d: 9.0, len: 5.0 }
export const POT_LUG_R = 6.0
/** CUI PJ-102AH: width, depth, height. Front face flush with the panel outer face */
export const DC_BODY = [9.0, 14.4, 11.0]
/** PJ-102AH axis above the PCB (datasheet, not in enclosure.py) */
export const DC_AXIS_H = 6.5
export const LED_H = 6.0
/** Traco TMA 1212D (PS1) body on the PCB: x0, x1, y0, y1 (PCB coordinates) */
export const DCDC_BOX = [65.5, 71.8, 2.8, 22.5]
export const DCDC_H = 10.2

export const BACK = {
  in: { x: JACK_IN_X, h: JACK_H },
  out: { x: JACK_OUT_X, h: JACK_H },
  dc: { x: DC_X, h: DC_AXIS_H },
}

export const FRONT = {
  pots: POT_X.map((x) => ({ x, h: POT_H })),
  led: { x: LED_X, h: LED_H },
}

export const axisZ = (h: number) => Z_PCB_TOP + h

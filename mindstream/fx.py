"""The effects' shaders: the programs the graphics card runs for each effect in effects.py.

Only text is here (no OpenGL), so they can be checked without a screen. gl_view.py compiles them when it starts; one
that will not compile on a given card is left out and said, and the rest carry on.

Every pass over the screen (PASSES) reads the picture so gone from `src` and writes the picture with its effect. They
are given: amount (how gone the effect is turned, 0 to 1), t (seconds), pulse (1 on the beat, dying away), beat (beats
so gone), resx and resy (the size of what is being drawn, in points).

Light and the screen's numbers. The screen's frame is worked in light (linear: values that add as light does, and may
pass white) up to the tone curve (OUTPUT), and the effects in effects.DISPLAY on the finished picture after it. Each
picture's own chain is worked on the picture as the screen shows it (0 to 1), and the surface turns it into light as
it draws it. So most passes run both ways, and are told which by `lin` (1: they are reading light). What changes with
it is small and kept in a few places: brightness (luma) is read as it looks (the screen's numbers, about light to the
power 1/2.2), so every threshold an effect was tuned on means what it meant; the bloom's bright-pass is judged the same
way; and the roll-off after a glow is left to the one tone curve at the end. (LINEAR)
"""

LINEAR = """
uniform float lin;
float luma(vec3 c) { float y = dot(c, vec3(0.299, 0.587, 0.114)); return lin > 0.5 ? pow(max(y, 0.0), 0.4545) : y; }
"""

# The sRGB curve both ways: pictures are stored as the screen shows them and turned into light when they are drawn; the
# frame is turned back at the end. Exact (the straight part near black included), and carried on past 1 for light
# brighter than white.
SRGB = """
vec3 toLinear(vec3 c) {
    c = max(c, 0.0);
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}
vec3 toDisplay(vec3 c) {
    c = max(c, 0.0);
    return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}
"""

HEAD = """
#version 330 core
in vec2 vUV;
uniform sampler2D src;
uniform float amount, t, pulse, beat, resx, resy;
out vec4 colour;
""" + LINEAR + """
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
vec2 hash22(vec2 p) { return fract(sin(vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)))) * 43758.5453); }
"""

RIPPLE = HEAD + """
void main() {
    float aspect = resx / resy;
    vec2 p = (vUV - 0.5) * vec2(aspect, 1.0);
    float r = length(p), phase = fract(beat);
    vec2 away = p / max(r, 1e-4), push = vec2(0.0);
    float shine = 0.0;
    for (int i = 0; i < 3; i++) {                              // the rings of the last three beats, each further out and fainter
        float age = phase + float(i);
        float d = r - age * 0.45;
        float env = exp(-d * d * 90.0) * exp(-age * 0.9);
        push += away * sin(d * 70.0) * env;
        shine += cos(d * 70.0) * env;
    }
    push += 0.22 * vec2(sin(p.y * 38.0 + t * 2.1), cos(p.x * 34.0 - t * 1.7));       // the water is never quite still
    vec3 c = texture(src, vUV + push * amount * 0.02 / vec2(aspect, 1.0)).rgb;
    c += vec3(0.9, 0.95, 1.0) * max(shine, 0.0) * amount * 0.25;                     // light on the crests
    colour = vec4(c, 1.0);
}
"""

SHATTER = HEAD + """
void main() {
    float aspect = resx / resy;
    float cells = mix(5.0, 16.0, amount);
    vec2 p = (vUV - 0.5) * vec2(aspect, 1.0) * cells;
    vec2 ip = floor(p), fp = fract(p);
    float d1 = 8.0, d2 = 8.0;
    vec2 best = vec2(0.0), cell = vec2(0.0);
    for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = 0.5 + 0.42 * sin(t * 0.35 + 6.2831 * hash22(ip + g));          // the cells drift
        vec2 r = g + o - fp;
        float d = dot(r, r);
        if (d < d1) { d2 = d1; d1 = d; best = r; cell = ip + g; } else if (d < d2) { d2 = d; }
    }
    float crack = sqrt(d2) - sqrt(d1);                                            // nothing at the line between two cells
    vec2 tilt = (hash22(cell + 17.0) - 0.5) * 2.0;                                // each cell bends the picture its own way
    vec2 uv = vUV + (tilt * 0.035 + best * 0.08 / cells) * amount * (1.0 + 0.6 * pulse);
    vec3 c = texture(src, uv).rgb;
    c *= mix(1.0, 0.85 + 0.3 * hash21(cell + 3.0), amount);                        // some facets catch more light
    c += smoothstep(0.06, 0.0, crack) * 0.35 * amount;                             // and the cracks catch it
    colour = vec4(c, 1.0);
}
"""

GLITCH = HEAD + """
float hash1(float n) { return fract(sin(n) * 43758.5453); }
void main() {
    float tick = floor(beat * 4.0);                                               // it changes on every sixteenth
    float burst = amount * (0.35 + 0.65 * pulse);
    vec2 uv = vUV;
    float band = floor(uv.y * mix(6.0, 40.0, hash1(tick * 1.7)));                 // bands that slip sideways
    if (hash21(vec2(band, tick + 9.0)) < burst * 0.6) uv.x += (hash21(vec2(band, tick)) - 0.5) * 0.25 * burst;
    vec2 block = floor(uv * vec2(12.0, 7.0));                                     // blocks that jump
    if (hash21(block + tick * 3.1) < burst * 0.18) uv += (hash22(block + 1.3 + tick) - 0.5) * 0.3 * burst;
    float tear = (hash1(floor(uv.y * resy * 0.5) + tick) - 0.5) * 0.004 * burst;  // fine tearing, line by line
    float sp = 0.012 * burst;
    vec3 c = vec3(texture(src, uv + vec2(sp + tear, 0.0)).r, texture(src, uv + vec2(tear, 0.0)).g, texture(src, uv - vec2(sp - tear, 0.0)).b);
    if (hash21(block * 1.9 + tick) < burst * 0.1) c = floor(c * 4.0 + 0.5) / 4.0; // some blocks lose their colours
    c += (hash21(vUV * vec2(resx, resy) + t) - 0.5) * 0.08 * burst;
    colour = vec4(c, 1.0);
}
"""

GYROID = HEAD + """
// a flight through an endless curved lattice: for every point of the screen a ray is walked forward until it meets it
vec2 path(float z) { return vec2(sin(z * 0.31) * 0.7, cos(z * 0.23) * 0.5); }
float map(vec3 p) {
    float shell = (abs(dot(sin(p), cos(p.yzx))) - (0.10 + 0.05 * pulse)) * 0.55;  // the wall of the lattice, breathing on the beat
    return max(shell, 0.42 - length(p.xy - path(p.z)));                           // a way through it is kept clear for the flight
}
vec3 normalAt(vec3 p) {
    vec2 e = vec2(0.003, 0.0);
    return normalize(vec3(map(p + e.xyy) - map(p - e.xyy), map(p + e.yxy) - map(p - e.yxy), map(p + e.yyx) - map(p - e.yyx)));
}
vec3 skin(vec3 p, vec3 n) {                                                       // the picture, laid on from three sides
    vec3 w = pow(abs(n), vec3(4.0));
    w /= (w.x + w.y + w.z);
    return texture(src, p.yz * 0.11 + 0.5).rgb * w.x + texture(src, p.zx * 0.11 + 0.5).rgb * w.y + texture(src, p.xy * 0.11 + 0.5).rgb * w.z;
}
void main() {
    vec2 q = (vUV - 0.5) * vec2(resx / resy, 1.0);
    float along = t * 0.55 + beat * 0.2;
    vec3 ro = vec3(path(along), along);
    vec3 look = normalize(vec3(path(along + 1.2), along + 1.2) - ro);
    vec3 right = normalize(cross(vec3(sin(t * 0.11) * 0.3, 1.0, 0.0), look)), up = cross(look, right);
    vec3 rd = normalize(look + q.x * right + q.y * up);
    float gone = 0.0, steps = 0.0;
    bool hit = false;
    for (int i = 0; i < 96; i++) {
        float d = map(ro + rd * gone);
        if (d < 0.0015 * (1.0 + gone)) { hit = true; break; }
        gone += d * 0.85;
        steps += 1.0;
        if (gone > 26.0) break;
    }
    vec3 behind = texture(src, vUV).rgb;                                          // a long way off, the lattice fades into the picture itself
    vec3 c = behind;
    if (hit) {
        vec3 p = ro + rd * gone, n = normalAt(p);
        float facing = max(dot(n, -rd), 0.0);
        float rim = pow(1.0 - facing, 3.0);
        float hollow = 1.0 - steps / 96.0;                                        // deep corners take longer to reach: they are darker
        vec3 lit = skin(p, n) * (0.25 + 0.95 * facing) * (0.4 + 0.6 * hollow) + rim * (0.25 + 0.5 * pulse) * (0.4 + behind);
        c = mix(behind, lit, exp(-gone * 0.11));
    }
    colour = vec4(mix(behind, c, smoothstep(0.0, 0.5, amount)), 1.0);
}
"""

PAINT = HEAD + """
// oil paint: around each point, the flattest of four neighbouring patches is taken, which keeps edges and loses detail
void main() {
    vec2 px = vec2(resy / 1080.0) / vec2(resx, resy);                             // strokes the same size whatever the screen
    int radius = int(2.0 + amount * 6.0);
    vec3 m0 = vec3(0.0), m1 = vec3(0.0), m2 = vec3(0.0), m3 = vec3(0.0), s0 = vec3(0.0), s1 = vec3(0.0), s2 = vec3(0.0), s3 = vec3(0.0);
    for (int j = 0; j <= radius; j++) for (int i = 0; i <= radius; i++) {
        vec2 o = vec2(float(i), float(j)) * px;
        vec3 c = texture(src, vUV + o * vec2(-1.0, -1.0)).rgb; m0 += c; s0 += c * c;
        c = texture(src, vUV + o * vec2(1.0, -1.0)).rgb; m1 += c; s1 += c * c;
        c = texture(src, vUV + o * vec2(-1.0, 1.0)).rgb; m2 += c; s2 += c * c;
        c = texture(src, vUV + o).rgb; m3 += c; s3 += c * c;
    }
    float n = float((radius + 1) * (radius + 1));
    m0 /= n; m1 /= n; m2 /= n; m3 /= n;
    float v0 = luma(abs(s0 / n - m0 * m0)), v1 = luma(abs(s1 / n - m1 * m1)), v2 = luma(abs(s2 / n - m2 * m2)), v3 = luma(abs(s3 / n - m3 * m3));
    vec3 c = m0;
    float least = v0;
    if (v1 < least) { least = v1; c = m1; }
    if (v2 < least) { least = v2; c = m2; }
    if (v3 < least) { c = m3; }
    colour = vec4(mix(texture(src, vUV).rgb, c, smoothstep(0.0, 0.15, amount)), 1.0);
}
"""

EDGES = HEAD + """
void main() {
    vec2 px = vec2(resy / 720.0) / vec2(resx, resy);
    float a = luma(texture(src, vUV + px * vec2(-1.0, 1.0)).rgb), b = luma(texture(src, vUV + px * vec2(0.0, 1.0)).rgb), c = luma(texture(src, vUV + px * vec2(1.0, 1.0)).rgb);
    float d = luma(texture(src, vUV + px * vec2(-1.0, 0.0)).rgb), f = luma(texture(src, vUV + px * vec2(1.0, 0.0)).rgb);
    float g = luma(texture(src, vUV + px * vec2(-1.0, -1.0)).rgb), h = luma(texture(src, vUV + px * vec2(0.0, -1.0)).rgb), i = luma(texture(src, vUV + px * vec2(1.0, -1.0)).rgb);
    vec2 slope = vec2((c + 2.0 * f + i) - (a + 2.0 * d + g), (a + 2.0 * b + c) - (g + 2.0 * h + i));
    float line = smoothstep(0.08, 0.5, length(slope));
    vec3 base = texture(src, vUV).rgb;
    vec3 hue = 0.5 + 0.5 * cos(6.2831 * (atan(slope.y, slope.x) / 6.2831 + t * 0.05 + vec3(0.0, 0.33, 0.67)));   // coloured by which way the edge runs
    vec3 neon = mix(base, hue, 0.6) * line * (1.6 + 1.2 * pulse);
    colour = vec4(base * (1.0 - 0.8 * amount) + neon * amount * 1.8, 1.0);
}
"""

HALFTONE = HEAD + """
// printed in four inks: each a screen of dots at its own angle, bigger where there is more of that ink
float dots(vec2 p, float angle, float fineness, float ink) {
    float s = sin(angle), c = cos(angle);
    vec2 g = fract(mat2(c, -s, s, c) * p * fineness) - 0.5;
    float r = sqrt(clamp(ink, 0.0, 1.0)) * 0.72;
    return smoothstep(r + 0.06, r - 0.06, length(g));
}
void main() {
    vec2 p = (vUV - 0.5) * vec2(resx / resy, 1.0);
    float fineness = mix(120.0, 55.0, amount);
    vec3 c = texture(src, vUV).rgb;
    float k = 1.0 - max(c.r, max(c.g, c.b));
    vec3 cmy = (1.0 - c - k) / max(1.0 - k, 1e-4);
    float cy = dots(p, 0.262, fineness, cmy.x), ma = dots(p, 1.309, fineness, cmy.y), ye = dots(p, 0.0, fineness, cmy.z), bl = dots(p, 0.785, fineness, k);
    vec3 print = vec3(0.96, 0.94, 0.90) * (1.0 - cy * vec3(1.0, 0.0, 0.0)) * (1.0 - ma * vec3(0.0, 1.0, 0.0)) * (1.0 - ye * vec3(0.0, 0.0, 1.0)) * (1.0 - bl * 0.92);
    colour = vec4(mix(c, print, smoothstep(0.0, 0.35, amount)), 1.0);
}
"""

RAYS = HEAD + """
// shafts of light: each point looks back towards the light and gathers the brightness it passes on the way
void main() {
    vec2 light = 0.5 + 0.25 * vec2(sin(t * 0.13), cos(t * 0.17));
    vec2 stride = (vUV - light) * (0.9 / 96.0);
    vec2 uv = vUV - stride * hash21(gl_FragCoord.xy + fract(t) * 91.0);           // a little unevenness hides the steps
    vec3 gathered = vec3(0.0);
    float fade = 1.0;
    for (int i = 0; i < 96; i++) {
        uv -= stride;
        vec3 s = texture(src, uv).rgb;
        gathered += s * max(luma(s) - 0.55, 0.0) * fade;
        fade *= 0.975;
    }
    colour = vec4(texture(src, vUV).rgb + gathered * (3.0 / 36.5) * amount * (1.0 + 0.5 * pulse), 1.0);
}
"""

BOKEH = HEAD + """
// out of focus towards the edges: each point becomes a disc, and bright points count for more, so they open into discs of light
void main() {
    vec2 px = 1.0 / vec2(resx, resy);
    float off = length((vUV - 0.5) * vec2(resx / resy, 1.0));
    float radius = smoothstep(0.12, 0.8, off) * amount * 0.022 * resy;
    if (radius < 0.6) { colour = vec4(texture(src, vUV).rgb, 1.0); return; }
    vec3 sum = vec3(0.0);
    float weight = 0.0, turn = hash21(gl_FragCoord.xy) * 6.2831;
    for (int i = 0; i < 72; i++) {
        float f = sqrt((float(i) + 0.5) / 72.0), a = float(i) * 2.39996 + turn;   // a sunflower's spiral: even cover of the disc
        vec3 s = texture(src, vUV + vec2(cos(a), sin(a)) * f * radius * px).rgb;
        float w = 1.0 + 6.0 * pow(luma(s), 4.0);
        sum += s * w;
        weight += w;
    }
    colour = vec4(sum / weight, 1.0);
}
"""

PASSES = {"ripple": RIPPLE, "shatter": SHATTER, "glitch": GLITCH, "gyroid": GYROID, "paint": PAINT, "edges": EDGES, "halftone": HALFTONE,
          "rays": RAYS, "bokeh": BOKEH}

# ---- bloom and streak: the bright parts are taken, made small and soft in steps, built back up, and laid over the picture

DOWN = """
#version 330 core
in vec2 vUV;
uniform sampler2D src;
uniform float px, py, knee, lin;
out vec4 colour;
vec3 at(float x, float y) { return texture(src, vUV + vec2(x * px, y * py)).rgb; }
void main() {
    vec3 o = at(0.0, 0.0) * 0.125 + (at(-2.0, 2.0) + at(2.0, 2.0) + at(-2.0, -2.0) + at(2.0, -2.0)) * 0.03125
           + (at(0.0, 2.0) + at(-2.0, 0.0) + at(2.0, 0.0) + at(0.0, -2.0)) * 0.0625
           + (at(-1.0, 1.0) + at(1.0, 1.0) + at(-1.0, -1.0) + at(1.0, -1.0)) * 0.125;
    if (knee > 0.5) {                                                             // only what is bright goes on, eased in so nothing pops
        float bright = max(o.r, max(o.g, o.b));
        float seen = lin > 0.5 ? pow(bright, 0.4545) : bright;                    // judged as it looks, in light or not
        float soft = clamp(seen - 0.45, 0.0, 0.3);
        float kept = max(soft * soft / 0.6, seen - 0.6) / max(seen, 1e-4);
        o *= lin > 0.5 ? pow(kept, 2.2) : kept;                                   // (that share of how it looks, in light)
    }
    colour = vec4(o, 1.0);
}
"""

UP = """
#version 330 core
in vec2 vUV;
uniform sampler2D src;
uniform float px, py;
out vec4 colour;
vec3 at(float x, float y) { return texture(src, vUV + vec2(x * px, y * py)).rgb; }
void main() {
    vec3 o = at(0.0, 0.0) * 4.0 + (at(-1.0, 0.0) + at(1.0, 0.0) + at(0.0, -1.0) + at(0.0, 1.0)) * 2.0
           + at(-1.0, -1.0) + at(1.0, -1.0) + at(-1.0, 1.0) + at(1.0, 1.0);
    colour = vec4(o / 16.0, 1.0);
}
"""

SMEAR = """
#version 330 core
in vec2 vUV;
uniform sampler2D src;
uniform float px, stretch;
out vec4 colour;
void main() {                                                                     // sideways only
    vec3 sum = vec3(0.0);
    float weight = 0.0;
    for (int i = -24; i <= 24; i++) {
        float w = exp(-float(i * i) / 200.0);
        sum += texture(src, vUV + vec2(float(i) * px * stretch, 0.0)).rgb * w;
        weight += w;
    }
    colour = vec4(sum / weight, 1.0);
}
"""

LAY = """
#version 330 core
in vec2 vUV;
uniform sampler2D src, glow;
uniform float gain, tr, tg, tb, lin;
out vec4 colour;
void main() {
    vec3 c = texture(src, vUV).rgb + texture(glow, vUV).rgb * gain * vec3(tr, tg, tb);
    if (lin < 0.5)                                                                // on a picture: the brightest parts roll off instead of burning out flat
        c = mix(c, 0.8 + 0.2 * tanh((c - 0.8) / 0.2), step(0.8, c));              // (in light the one tone curve at the end does it)
    colour = vec4(c, 1.0);
}
"""

# ---- particles: the picture as a cloud of points that remember where they are (docs/research/06_visual_effects.md, E04).
#
# Each point's state is kept in three float textures, one texel a point (PARTICLES wide and high), worked on by one pass
# a frame (STEP, writing all three at once) into a second set, the two used by turns:
#   where    x, y, z (on the picture's own plane, as the surface lays it out), and its age in seconds   (32-bit floats)
#   moving   its velocity, and how long it lives                                                       (16-bit)
#   home     where on the picture it belongs (u, v), and how many times it has been born               (16-bit)
# A point is born at a bright place or an edge of the picture (the best of eight places drawn at random), lives a few
# seconds, and is born again: so a new picture is taken up by the cloud within a few seconds. While it lives it is
# carried by a field that neither piles points up nor thins them out (the curl of a slowly moving noise), pulled home
# by a spring, and blown outward on a kick. The spring is the way home: strong, the cloud is the picture; weak, it is
# smoke that keeps being born back into the picture. The points are drawn (POINTS_VS) with no vertex data: each reads
# its own texel, takes its colour from the picture at its home, and adds its light to the frame.

PARTICLES = (2048, 2048)                # 4,194,304 points at most: all of them at full, fewer as it is turned down

HASH = """
uint mixed(uint v) { uint s = v * 747796405u + 2891336453u; uint w = ((s >> ((s >> 28u) + 4u)) ^ s) * 277803737u; return (w >> 22u) ^ w; }
float rnd(uint v) { return float(mixed(v)) / 4294967295.0; }
"""

STEP = """
#version 330 core
uniform sampler2D where, moving, home, texA, texB;
uniform float blend, dt, t, aspect, spring, curl, kick, kx, ky, drag, life, born, seed;
layout(location = 0) out vec4 outWhere;
layout(location = 1) out vec4 outMoving;
layout(location = 2) out vec4 outHome;
""" + HASH + """
float corner(vec3 c) {
    ivec3 i = ivec3(c);
    return rnd((uint(i.x) * 73856093u) ^ (uint(i.y) * 19349663u) ^ (uint(i.z) * 83492791u));
}
float noise(vec3 p) {                                         // smooth noise on a lattice of integer-hashed corners
    vec3 i = floor(p), f = fract(p), u = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(corner(i), corner(i + vec3(1, 0, 0)), u.x), mix(corner(i + vec3(0, 1, 0)), corner(i + vec3(1, 1, 0)), u.x), u.y),
               mix(mix(corner(i + vec3(0, 0, 1)), corner(i + vec3(1, 0, 1)), u.x), mix(corner(i + vec3(0, 1, 1)), corner(i + vec3(1, 1, 1)), u.x), u.y), u.z);
}
float potential(vec2 q, float s) { return noise(vec3(q, s)) + 0.5 * noise(vec3(q * 2.03 + 7.1, s * 1.3 + 3.0)); }
vec3 picture(vec2 uv) { return mix(texture(texA, uv).rgb, texture(texB, uv).rgb, blend); }
float look(vec2 uv) { return dot(picture(uv), vec3(0.299, 0.587, 0.114)); }
vec3 plane(vec2 uv) { return vec3((uv.x - 0.5) * 2.0 * aspect, (0.5 - uv.y) * 2.0, 0.0); }
void main() {
    ivec2 me = ivec2(gl_FragCoord.xy);
    uint id = uint(me.y) * uint(textureSize(where, 0).x) + uint(me.x);
    vec4 w = texelFetch(where, me, 0), m = texelFetch(moving, me, 0), h = texelFetch(home, me, 0);
    vec3 p = w.xyz, v = m.xyz;
    float age = w.w, span = m.w, gen = h.z;
    vec2 at = h.xy;
    if (age >= span || float(me.y) >= born) {                 // born (again): at a bright place or an edge of the picture
        gen = mod(gen + 1.0, 1024.0);
        uint s = id * 2654435761u + uint(gen) * 40503u + uint(seed);
        float best = -1.0;
        for (int k = 0; k < 8; k++) {
            vec2 uv = vec2(rnd(s + uint(k) * 2u), rnd(s + uint(k) * 2u + 1u));
            float edge = abs(look(uv + vec2(0.004, 0.0)) - look(uv - vec2(0.004, 0.0))) + abs(look(uv + vec2(0.0, 0.004)) - look(uv - vec2(0.0, 0.004)));
            float score = look(uv) + 2.0 * edge + 0.3 * rnd(s + 97u + uint(k));
            if (score > best) { best = score; at = uv; }
        }
        p = plane(at) + vec3(rnd(s + 211u) - 0.5, rnd(s + 213u) - 0.5, rnd(s + 217u) - 0.5) * 0.01;
        v = vec3(0.0);
        age = 0.0;
        span = life * (0.5 + rnd(s + 219u));
    } else {
        vec2 q = p.xy * 1.3;                                  // carried by the curl of a slowly moving noise: no piling up, no thinning
        float e = 0.01, s = t * 0.15;
        vec2 flow = vec2(potential(q + vec2(0.0, e), s) - potential(q - vec2(0.0, e), s),
                         potential(q - vec2(e, 0.0), s) - potential(q + vec2(e, 0.0), s)) / (2.0 * e);
        vec3 a = vec3(flow, 2.0 * (noise(vec3(q * 0.7 + 31.0, s)) - 0.5)) * curl;
        a += spring * (plane(at) - p) - 2.0 * sqrt(spring) * v;              // the way home: a spring, critically damped
        vec3 away = p - vec3(kx, ky, 0.0);                    // a kick: outward from a point, once
        v += normalize(away + vec3(0.0, 0.0, 1e-3)) * kick * exp(-dot(away.xy, away.xy) * 0.5);
        v += a * dt;
        v *= exp2(-dt / drag);                                // and the air holds it back, by half in `drag` seconds
        p += v * dt;
        age += dt;
    }
    outWhere = vec4(p, age);
    outMoving = vec4(v, span);
    outHome = vec4(at, gen, 1.0);
}
"""

POINTS_VS = """
#version 330 core
uniform mat4 mvp;
uniform sampler2D where, moving, home, texA, texB;
uniform float blend, size;
out vec3 vCol;
out float vFade;
""" + HASH + SRGB + """
void main() {
    ivec2 n = textureSize(where, 0), me = ivec2(gl_VertexID % n.x, gl_VertexID / n.x);
    vec4 w = texelFetch(where, me, 0);
    vec2 at = texelFetch(home, me, 0).xy;
    float lived = clamp(w.w / max(texelFetch(moving, me, 0).w, 1e-3), 0.0, 1.0);
    vFade = smoothstep(0.0, 0.08, lived) * (1.0 - smoothstep(0.8, 1.0, lived));        // born and gone softly, never popping
    vCol = toLinear(mix(texture(texA, at).rgb, texture(texB, at).rgb, blend));      // its home's colour, as light
    gl_Position = mvp * vec4(w.xyz, 1.0);
    gl_PointSize = max(size * (0.6 + 0.8 * rnd(uint(gl_VertexID))) / max(gl_Position.w, 0.2), 1.0);
}
"""

POINTS_FS = """
#version 330 core
in vec3 vCol;
in float vFade;
uniform float alpha;
out vec4 colour;
void main() {
    float soft = smoothstep(0.5, 0.1, length(gl_PointCoord - 0.5));               // a soft round point, its light added to the frame
    colour = vec4(vCol * soft * alpha * vFade, 1.0);
}
"""

MOST_POINTS = PARTICLES[0] * PARTICLES[1]

# ---- the last passes: the frame's light brought down to what the screen can show, and put on the screen.
#
# One program, two jobs (`tone`, `finish`): the lens and the colours pulled apart on the beat (both on light), then
# exposure (stops), the tone curve and the sRGB curve back to the screen's numbers, then the vignette and the tint
# (on what is seen, as before); and, finishing, grain and a dither of about one step. With no effect working on the
# finished picture, the one pass does both, straight to the screen. Otherwise the curve goes into a framebuffer, the
# effects in effects.DISPLAY run on that, and the last pass only finishes.
#
# The tone curve (`tonemap`, 0 to 1): at 0 the picture is left exactly as it is, and only light past white is brought
# in, by taking its colour towards white (as a bright thing burns out on film) rather than clipping each colour on its
# own (which turns hues); at 1, a film's curve on the brightness (the fitted filmic curve, on luminance so the hue is
# kept), which rolls highlights off from well below white and deepens the shadows; between, the two mixed. The rest
# position is 0, so that a picture with nothing on comes out as it went in (within the dither's step).

OUTPUT = """
#version 330 core
in vec2 vUV;
uniform sampler2D scene;
uniform float pulse, chaos, flat_, split, tintR, tintG, tintB, lens, grain, t, exposure, tonemap, tone, finish, frame;
out vec4 colour;
""" + HASH + SRGB + """
vec3 burn(vec3 c) {                                           // past white: towards white, keeping what it can of the colour
    float m = max(c.r, max(c.g, c.b));
    if (m <= 1.0) return c;
    return mix(c / m, vec3(1.0), (m - 1.0) / (m + 1.0));
}
vec3 film(vec3 c) {
    float y = dot(c, vec3(0.2126, 0.7152, 0.0722)), x = 0.8 * y;
    float f = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14);
    return burn(c * (f / max(y, 1e-6)));
}
float ign(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
void main() {
    vec2 d = vUV - 0.5;
    vec3 c;
    if (tone > 0.5) {
        float ab = (0.002 + 0.012 * pulse) * chaos * split * (1.0 - 0.7 * flat_);
        if (lens > 0.004) {                                   // lens: the picture bulges, and its colours part like a rainbow towards the edges
            float k = 0.45 * lens, spread = ab + 0.03 * lens;
            vec2 bent = d * (1.0 + k * dot(d, d)) / (1.0 + k * 0.25);
            vec3 sum = vec3(0.0), weight = vec3(0.0);
            for (int i = 0; i < 8; i++) {
                float f = float(i) / 7.0;
                vec3 w = max(1.0 - abs(f - vec3(0.0, 0.5, 1.0)) * 2.0, 0.0);
                sum += texture(scene, 0.5 + bent * (1.0 + (0.5 - f) * 2.0 * spread)).rgb * w;
                weight += w;
            }
            c = sum / weight;
        } else {
            c = vec3(texture(scene, vUV + d * ab).r, texture(scene, vUV).g, texture(scene, vUV - d * ab).b);
        }
        c = max(c, 0.0) * exp2(exposure);
        c = toDisplay(mix(burn(c), film(c), tonemap));
        c *= 1.0 - 0.55 * dot(d, d);
        c *= mix(vec3(1.0), vec3(tintR, tintG, tintB), 0.55);
    } else {
        c = texture(scene, vUV).rgb;
    }
    if (finish > 0.5) {
        if (grain > 0.004) {                                  // grain: film grain, more in the dark, and faint scan lines
            float n = rnd(uint(gl_FragCoord.x) * 1973u + uint(gl_FragCoord.y) * 9277u + uint(frame) * 26699u) - 0.5;
            c += n * 0.2 * grain * (1.0 - 0.6 * dot(c, vec3(0.333)));
            c *= 1.0 - 0.10 * grain * (0.5 + 0.5 * sin(gl_FragCoord.y * 3.14159));
        }
        float a = ign(gl_FragCoord.xy + 5.588238 * mod(frame, 64.0));                   // a dither of about a step, either way:
        float b = rnd(uint(gl_FragCoord.x) * 7919u + uint(gl_FragCoord.y) * 104729u + uint(frame) * 1299709u);     // slow fades do not band
        c += (a + b - 1.0) / 255.0;
    }
    colour = vec4(c, 1.0);
}
"""

# ---- a picture turned the screen's way up (and back). A picture's texture starts with its top row; the screen's
#      frame with its bottom one. Each picture's own effects (the "image" target) are run on it turned the screen's way,
#      so the glyphs stand upright and the lamp, the rays and the tape roll go the same way as on the screen.

FLIP = """
#version 330 core
in vec2 vUV;
uniform sampler2D src;
out vec4 colour;
void main() { colour = vec4(texture(src, vec2(vUV.x, 1.0 - vUV.y)).rgb, 1.0); }
"""

from . import fx2                         # the second set: the effects that remember, and the heavy ones

ALL = {**{f"pass:{key}": text for key, text in PASSES.items()}, "down": DOWN, "up": UP, "smear": SMEAR, "lay": LAY, "points": POINTS_FS, "flip": FLIP,
       "pt:step": STEP, **fx2.ALL}
VERTEX = {"points": POINTS_VS}           # the programs drawn with a vertex shader of their own (the rest are drawn over the whole target)
NEEDS = {**fx2.NEEDS, "particles": ("pt:step", "points")}     # the programs each effect needs, where that is not just its own pass


def needs(key):
    return NEEDS.get(key, ("pass:" + key,))

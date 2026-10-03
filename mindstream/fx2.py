"""The second set of effects' shaders: the ones that remember, and the heavy ones.

The first set (fx.py) are filters: each frame is treated afresh, so they can obscure a picture but cannot lose it
and bring it back. Most of these keep something from frame to frame (a fluid, a growing pattern, a smeared image,
the last second of frames), and each has a way home built in: how fast the true picture is let back in. That
return is what lets the picture be nearly lost and then come back.

How each is built follows docs/research/06_visual_effects.md, which gives the sources. Only text is here (no
OpenGL): gl_view.py compiles these and runs the passes, and keeps what each remembers.
"""

HEAD = """
#version 330 core
in vec2 vUV;
out vec4 colour;
uniform float lin;                                            // reading light (the screen's frame before the tone curve): see fx.py
float luma(vec3 c) { float y = dot(c, vec3(0.299, 0.587, 0.114)); return lin > 0.5 ? pow(max(y, 0.0), 0.4545) : y; }
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
"""

COPY = HEAD + """
uniform sampler2D src;
void main() { colour = vec4(texture(src, vUV).rgb, 1.0); }
"""

# ---- echo: the video-synth loop. The frame is fed back through a small turn and zoom, crawling along its own light.

ECHO = HEAD + """
uniform sampler2D src, last;
uniform float amount, t, dt, pulse, resx, resy;
vec3 hue(vec3 c, float a) {                                   // turned about the grey axis
    const vec3 k = vec3(0.57735);
    return c * cos(a) + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - cos(a));
}
void main() {
    float aspect = resx / resy;
    vec2 p = (vUV - 0.5) * vec2(aspect, 1.0);
    float r = length(p);
    float zoom = exp(-(0.25 + 0.9 * amount) * dt * (1.0 + 2.5 * pulse) * (0.6 + 0.8 * r));     // faster at the rim: a tunnel; a kick pushes it
    float turn = 0.35 * amount * dt * (1.0 + 1.5 * sin(t * 0.21));
    vec2 q = mat2(cos(turn), -sin(turn), sin(turn), cos(turn)) * p * zoom;
    vec2 uv = q / vec2(aspect, 1.0) + 0.5;
    vec2 px = 3.0 / vec2(resx, resy);                         // and it crawls along the slope of its own brightness, like oil
    vec2 slope = vec2(luma(texture(last, uv + vec2(px.x, 0.0)).rgb) - luma(texture(last, uv - vec2(px.x, 0.0)).rgb),
                      luma(texture(last, uv + vec2(0.0, px.y)).rgb) - luma(texture(last, uv - vec2(0.0, px.y)).rgb));
    uv += slope * px * (0.7 + 2.0 * amount);
    vec3 f = texture(last, uv).rgb;
    f = hue(f, radians(0.6 + 1.6 * amount) * 60.0 * dt);      // its colour turns as it ages
    f = mix(vec3(dot(f, vec3(0.299, 0.587, 0.114))), f, 1.04);       // a little more colour each time round, or the loop greys out
    f *= pow(0.5, dt / mix(0.25, 3.0, amount) * (lin > 0.5 ? 2.2 : 1.0));     // and it fades, to look half as bright in this many seconds
    f /= 1.0 + max(luma(f) - 0.9, 0.0);                       // it cannot run away
    vec3 s = texture(src, vUV).rgb;
    float back = clamp(mix(1.0, 0.04, amount) + 0.2 * pulse * amount, 0.0, 1.0);          // the way home: how much true picture is let in
    colour = vec4(mix(f, s, back), 1.0);
}
"""

# ---- mosh: the picture stops being renewed and is dragged about by the motion of what should have replaced it

SMALL = HEAD + """
uniform sampler2D src;
uniform float px, py;
void main() {                                                 // brightness, softened: what the motion is read from
    float l = luma(texture(src, vUV).rgb) * 0.4;
    l += 0.15 * (luma(texture(src, vUV + vec2(px, 0.0)).rgb) + luma(texture(src, vUV - vec2(px, 0.0)).rgb)
               + luma(texture(src, vUV + vec2(0.0, py)).rgb) + luma(texture(src, vUV - vec2(0.0, py)).rgb));
    colour = vec4(l, 0.0, 0.0, 1.0);
}
"""

FLOW = HEAD + """
uniform sampler2D now, before;
uniform float px, py;
void main() {                                                 // how each place has moved since the last frame
    vec2 ox = vec2(2.0 * px, 0.0), oy = vec2(0.0, 2.0 * py);
    vec2 slope = vec2(texture(now, vUV + ox).r - texture(now, vUV - ox).r + texture(before, vUV + ox).r - texture(before, vUV - ox).r,
                      texture(now, vUV + oy).r - texture(now, vUV - oy).r + texture(before, vUV + oy).r - texture(before, vUV - oy).r) / 8.0;
    float change = texture(now, vUV).r - texture(before, vUV).r;
    vec2 v = -change * slope / (dot(slope, slope) + 0.0006);
    float moved = length(v);
    v *= smoothstep(0.15, 0.5, moved) * min(1.0, 6.0 / max(moved, 1e-4));           // small ones are noise; none longer than six points
    colour = vec4(v * vec2(px, py), 0.0, 1.0);
}
"""

MOSH = HEAD + """
uniform sampler2D src, last, flow;
uniform float amount, t, keyframe, resx, resy;
void main() {
    vec2 blocks = vec2(resx, resy) / 16.0;                    // in blocks sixteen points square, as a film coder works
    vec2 block = floor(vUV * blocks);
    vec2 v = texture(flow, (block + 0.5) / blocks).rg;
    vec3 held = texture(last, vUV - v * (1.0 + 2.0 * amount)).rgb;
    vec3 s = texture(src, vUV).rgb;
    float heals = step(hash21(block + floor(t * 24.0) * 0.37), mix(0.5, 0.003, amount));    // a block is renewed now and then
    float still = (1.0 - smoothstep(0.0003, 0.002, length(v))) * mix(1.0, 0.02, amount);   // what is not moving comes through
    colour = vec4(mix(held, s, clamp(max(max(heals, still), keyframe), 0.0, 1.0)), 1.0);   // and on the bar line, the whole picture
}
"""

# ---- fluid: the picture's colours carried in a swirling flow that cannot be squeezed. Speeds are in grid points a second.

ADVECT = HEAD + """
uniform sampler2D field, vel;
uniform float dt, px, py, keep;
void main() { colour = vec4(texture(field, vUV - dt * texture(vel, vUV).xy * vec2(px, py)).xyz * keep, 1.0); }
"""

FORCE = HEAD + """
uniform sampler2D vel, src;
uniform float dt, t, pulse, amount, cx, cy, aspect, px, py;
float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash21(i), hash21(i + vec2(1, 0)), f.x), mix(hash21(i + vec2(0, 1)), hash21(i + vec2(1, 1)), f.x), f.y);
}
float field(vec2 p) { return vnoise(p) + 0.5 * vnoise(p * 2.03 + 7.1); }
float spin(vec2 uv) {
    return 0.5 * ((texture(vel, uv + vec2(px, 0.0)).y - texture(vel, uv - vec2(px, 0.0)).y)
                - (texture(vel, uv + vec2(0.0, py)).x - texture(vel, uv - vec2(0.0, py)).x));
}
void main() {
    vec2 v = texture(vel, vUV).xy;
    vec2 p = (vUV - vec2(cx, cy)) * vec2(aspect, 1.0);
    v += p / max(length(p), 1e-4) * exp(-dot(p, p) / 0.02) * pulse * 2600.0 * amount * dt;        // each kick pushes outward from a point
    vec2 f = vUV * vec2(aspect, 1.0) * 2.5 + vec2(t * 0.03, -t * 0.02);                           // something always stirs it, slowly
    v += vec2(field(f + vec2(0.0, 0.01)) - field(f - vec2(0.0, 0.01)), field(f - vec2(0.01, 0.0)) - field(f + vec2(0.01, 0.0))) / 0.02 * 25.0 * amount * dt;
    v.y += (luma(texture(src, vUV).rgb) - 0.4) * 40.0 * amount * dt;                              // what is bright rises
    float w = spin(vUV);                                                                          // and the small swirls are put back
    vec2 lean = vec2(abs(spin(vUV + vec2(px, 0.0))) - abs(spin(vUV - vec2(px, 0.0))), abs(spin(vUV + vec2(0.0, py))) - abs(spin(vUV - vec2(0.0, py))));
    lean /= max(length(lean), 1e-4);
    v += 8.0 * vec2(lean.y, -lean.x) * w * dt;
    float fast = length(v);
    colour = vec4(v * min(1.0, 1200.0 / max(fast, 1e-4)), 0.0, 1.0);
}
"""

DIVERGE = HEAD + """
uniform sampler2D vel;
uniform float px, py;
void main() {
    colour = vec4(0.5 * (texture(vel, vUV + vec2(px, 0.0)).x - texture(vel, vUV - vec2(px, 0.0)).x
                       + texture(vel, vUV + vec2(0.0, py)).y - texture(vel, vUV - vec2(0.0, py)).y), 0.0, 0.0, 1.0);
}
"""

JACOBI = HEAD + """
uniform sampler2D press, div;
uniform float px, py;
void main() {
    colour = vec4((texture(press, vUV + vec2(px, 0.0)).r + texture(press, vUV - vec2(px, 0.0)).r
                 + texture(press, vUV + vec2(0.0, py)).r + texture(press, vUV - vec2(0.0, py)).r - texture(div, vUV).r) * 0.25, 0.0, 0.0, 1.0);
}
"""

PROJECT = HEAD + """
uniform sampler2D vel, press;
uniform float px, py;
void main() {
    vec2 slope = vec2(texture(press, vUV + vec2(px, 0.0)).r - texture(press, vUV - vec2(px, 0.0)).r,
                      texture(press, vUV + vec2(0.0, py)).r - texture(press, vUV - vec2(0.0, py)).r);
    colour = vec4(texture(vel, vUV).xy - 0.5 * slope, 0.0, 1.0);
}
"""

DYE = HEAD + """
uniform sampler2D dye, vel, src;
uniform float dt, px, py, back;
void main() {                                                 // the colour is carried along, and a little true picture is let back in
    vec3 carried = texture(dye, vUV - dt * texture(vel, vUV).xy * vec2(px, py)).rgb;
    colour = vec4(mix(carried, texture(src, vUV).rgb, back), 1.0);
}
"""

# ---- slit: different parts of the frame show different moments of the last second

SLIT = HEAD + """
uniform sampler2D src;
uniform sampler2DArray ring;
uniform float amount, head, count, mode, f16, resx, resy;
void main() {
    vec2 p = (vUV - 0.5) * vec2(resx / resy, 1.0);
    float late;                                               // how far back each place looks: it changes every four bars
    if (mode < 0.5) late = vUV.y;
    else if (mode < 1.5) late = clamp(length(p) * 1.2, 0.0, 1.0);
    else if (mode < 2.5) late = 1.0 - luma(texture(src, vUV).rgb);
    else late = hash21(floor(vUV * vec2(9.0, 5.0)));
    float d = amount * (count - 2.0) * late;
    d = min(mix(d, floor(d / f16 + 0.5) * f16, step(0.5, amount)), count - 2.0);      // turned far, only moments that fell on a sixteenth
    float at = head - 1.0 - d, lo = floor(at);
    vec3 a = texture(ring, vec3(vUV, mod(lo + count, count))).rgb, b = texture(ring, vec3(vUV, mod(lo + 1.0 + count, count))).rgb;
    colour = vec4(mix(a, b, at - lo), 1.0);
}
"""

# ---- coral: two chemicals that make pattern of themselves, fed along the picture's edges

GROW = HEAD + """
uniform sampler2D state, src;
uniform float px, py, seed, fresh;
void main() {
    vec2 c = texture(state, vUV).rg;
    vec2 ox = vec2(px, 0.0), oy = vec2(0.0, py);
    vec2 lap = -c + 0.2 * (texture(state, vUV + ox).rg + texture(state, vUV - ox).rg + texture(state, vUV + oy).rg + texture(state, vUV - oy).rg)
             + 0.05 * (texture(state, vUV + ox + oy).rg + texture(state, vUV + ox - oy).rg + texture(state, vUV - ox + oy).rg + texture(state, vUV - ox - oy).rg);
    float light = luma(texture(src, vUV).rgb);
    float feed = mix(0.029, 0.0545, light), kill = mix(0.057, 0.062, light);          // mazes in the dark, coral in the light
    float a = c.r, b = c.g, eaten = a * b * b;
    a += lap.r - eaten + feed * (1.0 - a);
    b += 0.5 * lap.g + eaten - (kill + feed) * b;
    float edge = length(vec2(luma(texture(src, vUV + 2.0 * ox).rgb) - luma(texture(src, vUV - 2.0 * ox).rgb),
                             luma(texture(src, vUV + 2.0 * oy).rgb) - luma(texture(src, vUV - 2.0 * oy).rgb)));
    b += smoothstep(0.08, 0.3, edge) * seed;                                          // it keeps growing out of the picture's lines
    if (fresh > 0.5) { a = 1.0; b = max(step(0.2, edge), step(0.996, hash21(floor(vUV * vec2(200.0, 110.0))))); }
    colour = vec4(clamp(a, 0.0, 1.0), clamp(b, 0.0, 1.0), 0.0, 1.0);
}
"""

CORAL = HEAD + """
uniform sampler2D src, state;
uniform float amount, px, py, t;
void main() {                                                 // the pattern shown as a wet, raised skin over the picture
    float b = texture(state, vUV).g;
    vec3 n = normalize(vec3(-6.0 * (texture(state, vUV + vec2(px, 0.0)).g - texture(state, vUV - vec2(px, 0.0)).g),
                            -6.0 * (texture(state, vUV + vec2(0.0, py)).g - texture(state, vUV - vec2(0.0, py)).g), 1.0));
    vec3 lamp = normalize(vec3(cos(t * 0.4), sin(t * 0.4), 0.7));
    float lit = max(dot(n, lamp), 0.0), shine = pow(max(reflect(-lamp, n).z, 0.0), 30.0);
    vec3 base = texture(src, vUV).rgb, through = texture(src, vUV + n.xy * 0.03 * amount).rgb;
    float mask = smoothstep(0.08, 0.3, b);
    vec3 grown = through * (0.5 + 0.8 * lit) * mix(vec3(1.0), vec3(1.15, 0.95, 0.8), mask) + shine * 0.5 * mask;
    colour = vec4(mix(base, mix(through, grown, mask * 0.9 + 0.1), smoothstep(0.0, 0.35, amount)), 1.0);
}
"""

# ---- sort: runs of the picture sorted by brightness, a step at a time, so that it is seen to melt

LATCH = HEAD + """
uniform sampler2D src;
uniform float amount, resx, resy, seedn;
void main() {                                                 // the picture taken, and which of it is to be sorted
    vec3 c = texture(src, vUV).rgb;
    vec2 px = 6.0 / vec2(resx, resy);
    float light = 0.2 * (luma(c) + luma(texture(src, vUV + vec2(px.x, 0.0)).rgb) + luma(texture(src, vUV - vec2(px.x, 0.0)).rgb)
                       + luma(texture(src, vUV + vec2(0.0, px.y)).rgb) + luma(texture(src, vUV - vec2(0.0, px.y)).rgb));
    float inside = step(mix(0.9, 0.12, amount), light);       // the brighter masses; more of it as the effect is turned up
    float column = floor(gl_FragCoord.x / 3.0);
    float run = mix(60.0, 420.0, amount) * (0.5 + hash21(vec2(column, seedn)));       // runs of uneven lengths
    if (mod(gl_FragCoord.y + hash21(vec2(column, seedn + 3.0)) * run, run) < 1.0) inside = 0.0;
    colour = vec4(c, inside);
}
"""

SORT = HEAD + """
uniform sampler2D state;
uniform int parity;
void main() {                                                 // one step: each point and its neighbour above or below, the darker one lower
    ivec2 me = ivec2(gl_FragCoord.xy), size = textureSize(state, 0);
    bool lower = ((me.y + parity) & 1) == 0;
    ivec2 other = me + ivec2(0, lower ? 1 : -1);
    vec4 a = texelFetch(state, me, 0);
    if (other.y < 0 || other.y >= size.y) { colour = a; return; }
    vec4 b = texelFetch(state, other, 0);
    if (a.a < 0.5 || b.a < 0.5) { colour = a; return; }
    float ka = luma(a.rgb), kb = luma(b.rgb);
    bool change = lower ? (ka > kb) : (kb > ka);
    colour = change ? vec4(b.rgb, a.a) : a;
}
"""

SORTED = HEAD + """
uniform sampler2D src, state;
uniform float amount;
void main() {
    vec4 s = texture(state, vUV);
    colour = vec4(mix(texture(src, vUV).rgb, s.rgb, s.a * smoothstep(0.0, 0.08, amount)), 1.0);
}
"""

# ---- droste and mobius: the picture folded into space that holds itself

DROSTE = HEAD + """
uniform sampler2D src;
uniform float amount, t, beat, resx, resy;
void main() {                                                 // the picture inside itself, down a spiral, for ever
    float aspect = resx / resy;
    vec2 z = (vUV - 0.5) * vec2(aspect, 1.0) * 2.0;
    float ratio = log(mix(9.0, 3.0, amount));                 // how much smaller each copy is
    vec2 w = vec2(log(length(z) + 1e-6), atan(z.y, z.x));
    float lean = -ratio / 6.28318;                            // one turn round the middle is one step of size: the spiral closes
    w = vec2(w.x - w.y * lean, w.x * lean + w.y);
    w.x = mod(w.x + t * 0.25 + beat * 0.1, ratio) - ratio;
    vec2 into = exp(w.x) * vec2(cos(w.y), sin(w.y)) * 0.5 / vec2(aspect, 1.0) + 0.5;
    colour = vec4(texture(src, mix(vUV, into, smoothstep(0.0, 0.4, amount))).rgb, 1.0);        // it folds in; it does not fade in
}
"""

MOBIUS = HEAD + """
uniform sampler2D src;
uniform float amount, t, resx, resy;
vec2 mul(vec2 a, vec2 b) { return vec2(a.x * b.x - a.y * b.y, a.x * b.y + a.y * b.x); }
vec2 over(vec2 a, vec2 b) { return mul(a, vec2(b.x, -b.y)) / dot(b, b); }
void main() {                                                 // the picture slid through itself: the middle swells, the far side shrinks to the rim
    float aspect = resx / resy;
    vec2 z = (vUV - 0.5) * vec2(aspect, 1.0) * 2.0;
    vec2 a = 0.72 * amount * vec2(cos(t * 0.3), sin(t * 0.23));
    vec2 w = over(z - a, vec2(1.0, 0.0) - mul(vec2(a.x, -a.y), z));
    colour = vec4(texture(src, w * 0.5 / vec2(aspect, 1.0) + 0.5).rgb, 1.0);
}
"""

# ---- relief: the flat picture as a raised thing, seen from a moving eye under a moving lamp

HEIGHT = HEAD + """
uniform sampler2D src;
uniform float px, py;
void main() {                                                 // height from brightness, in broad shapes and not in grain
    float wide = 0.0, close = 0.0;
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.7854;
        vec2 d = vec2(cos(a) * px, sin(a) * py);
        wide += luma(texture(src, vUV + d * 9.0).rgb);
        close += luma(texture(src, vUV + d * 3.0).rgb);
    }
    colour = vec4(0.6 * wide / 8.0 + 0.3 * close / 8.0 + 0.1 * luma(texture(src, vUV).rgb), 0.0, 0.0, 1.0);
}
"""

RELIEF = HEAD + """
uniform sampler2D src, height;
uniform float amount, t, pulse, resx, resy;
float high(vec2 uv) { return texture(height, uv).r; }
void main() {
    float deep = 0.06 * amount * (1.0 + 0.5 * pulse);
    vec3 eye = normalize(vec3(0.25 * sin(t * 0.37), 0.18 * cos(t * 0.29), 1.0));
    vec2 along = -eye.xy / eye.z * deep;
    float s = 0.0;
    for (int i = 0; i < 24; i++) {                            // down the line of sight until the surface is met
        if (1.0 - s <= high(vUV + along * s)) break;
        s += 1.0 / 24.0;
    }
    float lo = max(s - 1.0 / 24.0, 0.0), hi = s;
    for (int i = 0; i < 5; i++) {                             // and then closer, by halves, so the steps do not show
        float mid = 0.5 * (lo + hi);
        if (1.0 - mid <= high(vUV + along * mid)) hi = mid; else lo = mid;
    }
    vec2 uv = vUV + along * hi;
    vec2 px = 2.0 / vec2(resx, resy);
    vec3 n = normalize(vec3(-(high(uv + vec2(px.x, 0.0)) - high(uv - vec2(px.x, 0.0))) * 14.0 * amount,
                            -(high(uv + vec2(0.0, px.y)) - high(uv - vec2(0.0, px.y))) * 14.0 * amount, 0.2));
    vec3 lamp = normalize(vec3(cos(t * 0.5), sin(t * 0.5), 0.6));
    float here = high(uv), shade = 1.0;
    for (int i = 1; i <= 12; i++) {                           // what stands between here and the lamp throws its shadow
        float f = float(i) / 12.0;
        shade = min(shade, 1.0 - clamp((high(uv + lamp.xy * deep * 2.0 * f) - (here + lamp.z * f * 0.5)) * 6.0, 0.0, 1.0));
    }
    float lit = max(dot(n, lamp), 0.0), shine = pow(max(reflect(-lamp, n).z, 0.0), 40.0);
    vec3 made = texture(src, uv).rgb * (0.35 + 0.9 * lit * shade) + shine * shade * 0.6;
    colour = vec4(mix(texture(src, vUV).rgb, made, smoothstep(0.0, 0.25, amount)), 1.0);
}
"""

# ---- strobe, invert, cycle: the oldest live effects, on the beat. `flash` is made outside, where its rate is limited.

BEAT = HEAD + """
uniform sampler2D src;
uniform float strobe, invert, cycle, flash, hit, turn;
void main() {
    vec3 c = texture(src, vUV).rgb;
    if (cycle > 0.004) {                                      // brightness in six bands, each a colour, and the colours step round on the beat
        float light = luma(c), band = floor(light * 6.0) / 6.0;
        vec3 ink = 0.5 + 0.5 * cos(6.28318 * (band * 0.9 + turn * 0.167 + vec3(0.0, 0.33, 0.67)));
        c = mix(c, ink * (0.35 + 0.9 * light), cycle);
    }
    if (invert > 0.004) {                                     // light and dark changed over, the colours kept, in bands that alternate
        vec3 turned = clamp(c + (1.0 - 2.0 * luma(c)), 0.0, 1.0);
        c = mix(c, turned, invert * hit * step(0.5, fract(vUV.y * 4.0 + turn * 0.5)));
    }
    colour = vec4(c * (1.0 + 2.5 * strobe * flash), 1.0);
}
"""

# ---- fractal: a flight down an endless carved corridor whose walls are painted with the picture from one fixed place.
#      From anywhere else the picture lies shattered across the walls; as the flight passes that place it snaps whole.

FRACTAL = HEAD + """
uniform sampler2D src;
uniform float amount, t, pulse, beat, resx, resy;
float sponge(vec3 p) {
    vec3 d0 = abs(p) - vec3(1.0);
    float d = min(max(d0.x, max(d0.y, d0.z)), 0.0) + length(max(d0, 0.0));
    float s = 1.0;
    for (int m = 0; m < 4; m++) {
        vec3 a = mod(p * s, 2.0) - 1.0;
        s *= 3.0;
        vec3 r = abs(1.0 - 3.0 * abs(a));
        d = max(d, (min(max(r.x, r.y), min(max(r.y, r.z), max(r.z, r.x))) - 1.0) / s);
    }
    return d;
}
float map(vec3 p) {
    float turn = 0.25 * sin(t * 0.17) + p.z * 0.12 * amount + 0.1 * pulse;        // the corridor twists along its length
    p.xy = mat2(cos(turn), -sin(turn), sin(turn), cos(turn)) * p.xy;
    p.z = mod(p.z + 1.0, 2.0) - 1.0;
    return sponge(p);
}
vec3 normalAt(vec3 p, float e) {
    const vec2 k = vec2(1.0, -1.0);
    return normalize(k.xyy * map(p + k.xyy * e) + k.yyx * map(p + k.yyx * e) + k.yxy * map(p + k.yxy * e) + k.xxx * map(p + k.xxx * e));
}
void main() {
    float aspect = resx / resy;
    vec2 q = (vUV - 0.5) * vec2(aspect, 1.0);
    float along = t * 0.45 + beat * 0.12;
    vec3 ro = vec3(0.05 * sin(t * 0.31), 0.05 * cos(t * 0.23), along);
    vec3 rd = normalize(vec3(q, 1.0));
    float gone = 0.02 + 0.03 * hash21(gl_FragCoord.xy), steps = 0.0;
    bool hit = false;
    for (int i = 0; i < 110; i++) {
        float d = map(ro + rd * gone);
        if (d < 0.0006 * (1.0 + gone * 3.0)) { hit = true; break; }
        gone += d * 0.9;
        steps += 1.0;
        if (gone > 14.0) break;
    }
    vec3 behind = texture(src, vUV).rgb, c = behind;
    if (hit) {
        vec3 p = ro + rd * gone, n = normalAt(p, 0.0008 * (1.0 + gone));
        vec3 from = vec3(0.0, 0.0, floor(along / 8.0) * 8.0 + 4.0);               // where the picture is thrown from: passed every eight units
        vec3 d = p - from;
        vec2 uv = d.xy / max(abs(d.z), 0.05) / vec2(aspect, 1.0) + 0.5;
        float facing = max(dot(n, -rd), 0.0), hollow = 1.0 - steps / 110.0;
        float shadow = 1.0, reach = 0.02;
        vec3 lamp = normalize(vec3(0.3, 0.5, -0.6));
        for (int i = 0; i < 24; i++) {                                            // one lamp, with soft shadows
            float h = map(p + n * 0.002 + lamp * reach);
            shadow = min(shadow, 12.0 * h / reach);
            reach += clamp(h, 0.01, 0.2);
            if (shadow < 0.02 || reach > 2.5) break;
        }
        shadow = clamp(shadow, 0.0, 1.0);
        vec3 lit = texture(src, uv).rgb * (0.3 + 0.6 * facing + 0.5 * max(dot(n, lamp), 0.0) * shadow) * (0.35 + 0.65 * hollow)
                 + pow(1.0 - facing, 3.0) * (0.15 + 0.4 * pulse) * (0.3 + behind);
        c = mix(behind, lit, exp(-gone * 0.16));
    }
    colour = vec4(mix(behind, c, smoothstep(0.0, 0.5, amount)), 1.0);
}
"""

# ---- vhs: the picture off a worn tape

VHS = HEAD + """
uniform sampler2D src;
uniform float amount, t, beat, resx, resy;
vec3 toYIQ(vec3 c) { return vec3(dot(c, vec3(0.299, 0.587, 0.114)), dot(c, vec3(0.596, -0.274, -0.322)), dot(c, vec3(0.211, -0.523, 0.312))); }
vec3 toRGB(vec3 c) { return vec3(c.x + 0.956 * c.y + 0.621 * c.z, c.x - 0.272 * c.y - 0.647 * c.z, c.x - 1.106 * c.y + 1.703 * c.z); }
void main() {
    vec2 uv = vUV;
    float line = floor(uv.y * 240.0);                         // two hundred and forty lines, as tape has
    uv.y = mix(uv.y, (line + 0.5) / 240.0, amount);
    uv.x += (sin(uv.y * 9.0 + t * 1.3) * 0.0015 + (hash21(vec2(line, floor(t * 60.0))) - 0.5) * 0.0012) * amount;      // the tape's speed wanders
    float roll = fract(t * 0.07 + 0.3 * floor(beat / 8.0));   // a tear in the tracking, rolling up the frame
    uv.x += smoothstep(0.02, 0.0, abs(uv.y - roll)) * amount * 0.06 * sin(t * 40.0);
    float foot = smoothstep(0.035, 0.0, vUV.y) * amount;      // where the heads change over, at the bottom
    uv.x += foot * (0.03 + 0.02 * sin(t * 13.0));
    float y = 0.0, sum = 0.0;
    vec2 iq = vec2(0.0);
    for (int i = -4; i <= 4; i++) {                           // brightness a little soft; colour five times softer, and late
        float o = float(i) / 4.0, w = 1.0 - abs(o) * 0.8;
        y += toYIQ(texture(src, uv + vec2(o * 0.0016 * (0.3 + amount), 0.0)).rgb).x * w;
        iq += toYIQ(texture(src, uv + vec2((o * 0.008 + 0.004) * amount, 0.0)).rgb).yz * w;
        sum += w;
    }
    vec3 c = toRGB(vec3(y, iq) / sum);
    c += (hash21(vec2(floor(uv.x * resx / 2.0), line + floor(t * 60.0) * 7.0)) - 0.5) * 0.12 * amount;
    c = mix(c, vec3(1.0), step(0.9985, hash21(vec2(floor(uv.x * 40.0), line * 3.1 + floor(t * 30.0)))) * amount);     // dropouts: short white streaks
    c = mix(c, vec3(hash21(vec2(uv.x * 300.0, t))), foot * 0.6);
    c *= 1.0 - 0.25 * amount * (0.5 + 0.5 * cos(vUV.y * 240.0 * 6.28318));
    colour = vec4(mix(texture(src, vUV).rgb, c, smoothstep(0.0, 0.2, amount)), 1.0);
}
"""

# ---- ascii: the picture as characters. Flat places by how dense a character is; edges by which way they run.

ASCII = HEAD + """
uniform sampler2D src, glyphs;
uniform float amount, resx, resy;
void main() {
    float wide = floor(mix(7.0, 20.0, amount) * resy / 1080.0 + 0.5), tall = floor(wide * 1.7 + 0.5);
    vec2 size = vec2(wide, tall), at = vUV * vec2(resx, resy);
    vec2 cell = floor(at / size), within = fract(at / size);
    vec2 centre = (cell + 0.5) * size / vec2(resx, resy), q = size / vec2(resx, resy) * 0.25;
    vec3 a = texture(src, centre + vec2(-q.x, -q.y)).rgb, b = texture(src, centre + vec2(q.x, -q.y)).rgb;
    vec3 c = texture(src, centre + vec2(-q.x, q.y)).rgb, d = texture(src, centre + vec2(q.x, q.y)).rgb;
    vec3 mean = (a + b + c + d) * 0.25;
    float light = luma(mean);
    vec2 slope = vec2(luma(b) + luma(d) - luma(a) - luma(c), luma(c) + luma(d) - luma(a) - luma(b));
    float which = floor(clamp(light, 0.0, 0.999) * 12.0);     // twelve characters from empty to full
    if (length(slope) > 0.35)                                 // and four strokes for an edge: upright, falling, level, rising
        which = 12.0 + mod(floor(atan(slope.y, slope.x) / 0.7854 + 0.5) + 8.0, 4.0);
    float ink = texture(glyphs, vec2((which + clamp(within.x, 0.04, 0.96)) / 16.0, 1.0 - within.y)).r;
    vec3 made = mean / max(light, 0.08) * (0.35 + 0.9 * light) * ink * 1.25 + mean * 0.06;
    colour = vec4(mix(texture(src, vUV).rgb, made, smoothstep(0.0, 0.15, amount)), 1.0);
}
"""

GLYPHS = " .:-=+*oa#%@|\\-/"            # the sixteen characters of the atlas, in the order the shader counts them

ALL = {"copy": COPY, "echo": ECHO, "small": SMALL, "flow": FLOW, "mosh": MOSH, "advect": ADVECT, "force": FORCE, "diverge": DIVERGE, "jacobi": JACOBI,
       "project": PROJECT, "dye": DYE, "slit": SLIT, "grow": GROW, "coral": CORAL, "latch": LATCH, "sort": SORT, "sorted": SORTED,
       "pass:droste": DROSTE, "pass:mobius": MOBIUS, "height": HEIGHT, "relief": RELIEF, "beat": BEAT, "pass:fractal": FRACTAL, "pass:vhs": VHS, "ascii": ASCII}
# the programs each effect needs, where that is not just its own pass
NEEDS = {"echo": ("echo",), "mosh": ("small", "flow", "mosh"), "fluid": ("advect", "force", "diverge", "jacobi", "project", "dye"), "slit": ("copy", "slit"),
         "coral": ("grow", "coral"), "sort": ("latch", "sort", "sorted"), "relief": ("height", "relief"), "strobe": ("beat",), "invert": ("beat",),
         "cycle": ("beat",), "ascii": ("ascii",), "bloom": ("down", "up", "lay"), "streak": ("down", "smear", "lay")}

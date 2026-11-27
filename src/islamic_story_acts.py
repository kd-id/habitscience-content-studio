"""Studio v10.5 — 4-Act Visual Storytelling & Animated Science Explainer Library.

Solves the "static Arabic wallpaper" problem across ALL 6 Studio v10 formats by enforcing a true
4-Act cinematic narrative arc where every Act looks completely different and directly visualizes
what the narrator is saying:

  - ACT 1 (`HOOK`,       0s .. ar_start)      : Dramatic full-screen Hook visual action (phone chaos,
                                                racing mind loops, heavy afternoon wall, anger heat,
                                                needle over ocean, flipping calendar, scroll envy).
                                                Arabic Dalil stays HIDDEN -> zero premature spoilers!
  - ACT 2 (`DALIL`,      ar_start .. ar_end)  : Sacred Center-Stage Reveal synced 100% to real Arabic VO
                                                (Syaikh Mishary Alafasy Qari / ar-SA-HamedNeural) with
                                                Amiri calligraphy, citation pill & illuminated translation.
  - ACT 3 (`EXPLAINER`,  ar_end .. climax_t)  : Arabic card EXITS cleanly! Replaced by live animated
                                                visual explainer diagrams directly teaching the brain/habit
                                                science (brain-wave calm curve, charging focus battery,
                                                1/3 balance pie chart, posture anger cool-down, 4-pillar
                                                constellation map, or before-vs-after shift cards).
  - ACT 4 (`CLIMAX`,     climax_t .. end)     : Emotional transformation payoff + unmistakable bold
                                                CORE LESSON takeaway card + soft Save & Share closing!
"""

from __future__ import annotations

from typing import Any


def resolve_story_acts(topic_meta: dict[str, Any] | None, scenes_meta: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive topic-matched Act 1 Hook visual, Act 3 Science Explainer visual, and Act 4 Core Lesson."""
    meta = topic_meta or {}
    dalil = meta.get("dalil") if isinstance(meta.get("dalil"), dict) else {}
    topic = str(meta.get("topic") or "").strip()
    low = (topic + " " + str(meta.get("angle") or "") + " " + str(dalil.get("citation") or "")).lower()

    # Default sensible narrative visuals
    hook_vis = "racing_mind"
    exp_vis = "brain_wave_calm"
    before_lbl = "NOISY AUTOPILOT"
    after_lbl = "CALM SUNNAH RHYTHM"
    stat_badge = "STRESS LOOP -> CALM CLARITY"
    core_lesson = "One calm sincere step today changes everything."
    hook_kicker = "STOP & NOTICE THIS"

    if any(k in low for k in ("needle", "ocean", "2577", "small dua")):
        hook_vis = "needle_ocean"
        exp_vis = "before_after_cards"
        before_lbl = "SCARCITY & SMALL FEARS"
        after_lbl = "BOUNDLESS TRUST & COURAGE"
        stat_badge = "ABUNDANCE MINDSET UNLOCKED"
        core_lesson = "Ask Allah boldly — His ocean never runs dry."
        hook_kicker = "PICTURE THIS"
    elif any(k in low for k in ("angry", "anger", "4782", "sit down")):
        hook_vis = "anger_heat"
        exp_vis = "posture_cool_down"
        before_lbl = "STANDING IN HEAT & REACTION"
        after_lbl = "SITTING BREAKS THE SURGE"
        stat_badge = "POSTURE SHIFT COOLS THE BRAIN"
        core_lesson = "When anger rises — sit down before you speak."
        hook_kicker = "THE INSTANT RESET"
    elif any(k in low for k in ("1/3", "one third", "stomach", "2380", "overeating")):
        hook_vis = "heavy_wall"
        exp_vis = "one_third_pie"
        before_lbl = "HEAVY MEAL -> BRAIN FOG"
        after_lbl = "1/3 FOOD • 1/3 WATER • 1/3 BREATH"
        stat_badge = "LIGHT ENERGY ALL AFTERNOON"
        core_lesson = "Stop at 1/3 food so your mind stays sharp."
        hook_kicker = "WHY YOU CRASH AFTER LUNCH"
    elif any(k in low for k in ("al-kahf", "kahf", "6470", "4 modern traps")):
        hook_vis = "racing_mind"
        exp_vis = "four_pillar_map"
        before_lbl = "4 HIDDEN MODERN TRAPS"
        after_lbl = "FAITH • WEALTH • KNOWLEDGE • POWER"
        stat_badge = "WEEKLY MENTAL COMPASS"
        core_lesson = "Read Al-Kahf every Friday to anchor your heart."
        hook_kicker = "4 TRAPS EVERY WEEK"
    elif any(k in low for k in ("friday", "jumuah", "jumu'ah", "854")):
        hook_vis = "rushing_calendar"
        exp_vis = "focus_battery_charge"
        before_lbl = "6 DAYS OF NONSTOP NOISE"
        after_lbl = "WEEKLY SPIRITUAL & MIND RESET"
        stat_badge = "CALM BATTERY RESTORED"
        core_lesson = "Pause the rush — honor Friday as your reset."
        hook_kicker = "YOUR WEEKLY RESET"
    elif any(k in low for k in ("waking up early", "2606", "early morning", "barakah", "fajr")):
        hook_vis = "phone_chaos"
        exp_vis = "focus_battery_charge"
        before_lbl = "LATE WAKE + INSTANT SCROLL"
        after_lbl = "20 QUIET MINUTES AT DAWN"
        stat_badge = "1 DAWN HOUR > 3 NOISY HOURS"
        core_lesson = "Guard 20 quiet phone-free minutes after Fajr."
        hook_kicker = "THE HOUR MOST PEOPLE MISS"
    elif any(k in low for k in ("qailulah", "midday", "4431", "nap")):
        hook_vis = "heavy_wall"
        exp_vis = "focus_battery_charge"
        before_lbl = "2 PM CRASH + CAFFEINE LOOP"
        after_lbl = "20-MINUTE PROPHETIC QAILULAH"
        stat_badge = "AFTERNOON CLARITY RECHARGED"
        core_lesson = "Take a 20-minute midday rest instead of forcing."
        hook_kicker = "THE 2 PM WALL"
    elif any(k in low for k in ("worry", "overthinking", "6369", "laziness", "stuck")):
        hook_vis = "racing_mind"
        exp_vis = "brain_wave_calm"
        before_lbl = "WORRY + GRIEF FREEZES ACTION"
        after_lbl = "DUA + ONE CALM 5-MIN START"
        stat_badge = "CALM MIND BREAKS THE FREEZE"
        core_lesson = "Name the worry in Dua, then take 1 tiny step."
        hook_kicker = "WHY YOU FEEL STUCK"
    elif any(k in low for k in ("94:5", "hardship", "ease", "sharh")):
        hook_vis = "racing_mind"
        exp_vis = "brain_wave_calm"
        before_lbl = "PANIC SEES ONLY WALLS"
        after_lbl = "EASE IS ALREADY WITH HARDSHIP"
        stat_badge = "HOPE CALMS STRESS SIGNALS"
        core_lesson = "Look closely — ease is planted inside the trial."
        hook_kicker = "LOOK AT ONE WORD"
    elif any(k in low for k in ("shukr", "gratitude", "14:7", "ibrahim")):
        hook_vis = "comparison_scroll"
        exp_vis = "brain_wave_calm"
        before_lbl = "BRAIN HUNTS WHAT IS MISSING"
        after_lbl = "DAILY SHUKR REWIRES PEACE"
        stat_badge = "GRATITUDE SHIFTS YOUR FOCUS"
        core_lesson = "Name 3 quiet blessings tonight & say Alhamdulillah."
        hook_kicker = "WHY ENOUGH NEVER FEELS ENOUGH"
    elif any(k in low for k in ("13:28", "dhikr", "restless")):
        hook_vis = "racing_mind"
        exp_vis = "brain_wave_calm"
        before_lbl = "QUIET ROOM, LOUD MIND"
        after_lbl = "RHYTHMIC DHIKR SETTLES HEART"
        stat_badge = "RACING THOUGHTS -> STILLNESS"
        core_lesson = "Pause for 60 seconds of quiet Dhikr today."
        hook_kicker = "STILL LOUD INSIDE?"
    elif any(k in low for k in ("comparison", "2963", "social media")):
        hook_vis = "comparison_scroll"
        exp_vis = "before_after_cards"
        before_lbl = "SCROLLING HIGHLIGHT REELS"
        after_lbl = "GROUNDING IN GRATITUDE"
        stat_badge = "ENVY FADES -> CONTENTMENT"
        core_lesson = "Look at what you have — stop measuring online."
        hook_kicker = "THE COMPARISON TRAP"
    elif any(k in low for k in ("istiqamah", "6464", "small daily", "99:7", "atom")):
        hook_vis = "heavy_wall"
        exp_vis = "focus_battery_charge"
        before_lbl = "BIG BURST -> THURSDAY BURNOUT"
        after_lbl = "SMALL DAILY ISTIQAMAH"
        stat_badge = "TINY CONSISTENT STEPS COMPOUND"
        core_lesson = "Keep 1 tiny good habit alive every single day."
        hook_kicker = "WHY MOTIVATION FADES"
    elif any(k in low for k in ("sleep", "isha", "78:9", "bedtime", "6324")):
        hook_vis = "phone_chaos"
        exp_vis = "brain_wave_calm"
        before_lbl = "MIDNIGHT SCREEN + RACING MIND"
        after_lbl = "EARLY NIGHT + CALM DUA RESET"
        stat_badge = "DEEP RECOVERY SLEEP UNLOCKED"
        core_lesson = "Close your screen early & surrender the day."
        hook_kicker = "STEALING TOMORROW'S PEACE"
    elif any(k in low for k in ("fasting", "747", "monday")):
        hook_vis = "rushing_calendar"
        exp_vis = "focus_battery_charge"
        before_lbl = "CONSTANT SNACKING + FOG"
        after_lbl = "GENTLE SUNNAH FASTING CLARITY"
        stat_badge = "SELF-CONTROL & SHARP FOCUS"
        core_lesson = "Try gentle fasting to reset energy & focus."
        hook_kicker = "WHY FASTING FEELS SHARP"
    elif any(k in low for k in ("niyyah", "bukhari 1", "intention")):
        hook_vis = "phone_chaos"
        exp_vis = "before_after_cards"
        before_lbl = "BUSY HOURS ON AUTOPILOT"
        after_lbl = "3-SECOND SINCERE NIYYAH"
        stat_badge = "ORDINARY WORK -> PURPOSE"
        core_lesson = "Pause 3 seconds to renew your Niyyah before starting."
        hook_kicker = "WHERE DID TODAY GO?"
    elif any(k in low for k in ("smile", "1956", "charity")):
        hook_vis = "racing_mind"
        exp_vis = "brain_wave_calm"
        before_lbl = "TENSE FACES & DAILY STRESS"
        after_lbl = "ONE SINCERE SMILE = CHARITY"
        stat_badge = "CALMS TWO MINDS AT ONCE"
        core_lesson = "Offer one genuine warm smile today as charity."
        hook_kicker = "FREE CHARITY"
    elif any(k in low for k in ("tawakkul", "65:3", "hasbunallah", "3:173", "2:286", "overburdened")):
        hook_vis = "racing_mind"
        exp_vis = "before_after_cards"
        before_lbl = "TRYING TO CONTROL OUTCOMES"
        after_lbl = "HONEST EFFORT + PURE TAWAKKUL"
        stat_badge = "MENTAL WEIGHT RELEASED"
        core_lesson = "Give your honest effort — trust Allah with results."
        hook_kicker = "STOP CARRYING WHAT ISN'T YOURS"
    elif any(k in low for k in ("2:153", "sabr", "salah", "5 brief")):
        hook_vis = "rushing_calendar"
        exp_vis = "brain_wave_calm"
        before_lbl = "NONSTOP GRIND -> BURNOUT"
        after_lbl = "5 DAILY PRAYER PAUSES"
        stat_badge = "BUILT-IN STRESS INTERRUPTER"
        core_lesson = "Treat every Salah as a sacred pause for your mind."
        hook_kicker = "WHY BURNOUT HAPPENS"
    elif any(k in low for k in ("tongue", "6018", "silent", "concern you", "2317", "25:63")):
        hook_vis = "phone_chaos"
        exp_vis = "before_after_cards"
        before_lbl = "REACTING TO EVERY ARGUMENT"
        after_lbl = "DELIBERATE SILENCE & DIGNITY"
        stat_badge = "PROTECTED MENTAL ENERGY"
        core_lesson = "Speak good or keep silent — guard your peace."
        hook_kicker = "PROTECT YOUR ENERGY"

    # Allow explicit override from topic_meta / dalil if present
    custom_acts = meta.get("story_acts") if isinstance(meta.get("story_acts"), dict) else {}
    return {
        "hook_visual": str(custom_acts.get("hook_visual") or hook_vis),
        "explainer_visual": str(custom_acts.get("explainer_visual") or exp_vis),
        "hook_kicker": str(custom_acts.get("hook_kicker") or hook_kicker),
        "before_label": str(custom_acts.get("before_label") or before_lbl),
        "after_label": str(custom_acts.get("after_label") or after_lbl),
        "stat_badge": str(custom_acts.get("stat_badge") or stat_badge),
        "core_lesson": str(custom_acts.get("core_lesson") or core_lesson),
    }


# ---------------------------------------------------------------------------
# Reusable HTML5 Canvas JS Library for Act 1 Hook & Act 3 Animated Explainers
# Styled dynamically via a theme palette dict (`{bgCard, border, ink, muted, accent, warn, good, light}`)
# so every one of the 6 formats keeps its 100% distinct visual identity!
# ---------------------------------------------------------------------------

STORY_ACTS_JS = r"""
function computeFourActTiming(cfg) {
  const total = Math.max(cfg.total_dur || 30, 6);
  const ar = cfg.arabic_window;
  let arStart, arEnd;
  if (ar && ar.end > ar.start) {
    arStart = ar.start;
    arEnd = ar.end;
  } else {
    arStart = total * 0.22;
    arEnd = total * 0.46;
  }
  const rem = Math.max(total - arEnd, 3.5);
  let climaxStart = arEnd + rem * 0.66;
  // Snap Act 4 Climax cleanly to the start of the final spoken scene when sensible!
  if (cfg.scenes && cfg.scenes.length >= 3) {
    const lastSc = cfg.scenes[cfg.scenes.length - 1];
    if (lastSc && lastSc.start >= arEnd + 2.2 && lastSc.start <= total - 2.6) {
      climaxStart = lastSc.start;
    }
  }
  return { arStart, arEnd, climaxStart, total };
}

function getCurrentAct(t, acts) {
  if (t < acts.arStart - 0.05) {
    return { name: 'HOOK', num: 1, localT: Math.min(Math.max(t / Math.max(acts.arStart, 0.5), 0), 1) };
  }
  if (t <= acts.arEnd + 0.14) {
    return { name: 'DALIL', num: 2, localT: Math.min(Math.max((t - acts.arStart) / Math.max(acts.arEnd - acts.arStart, 0.5), 0), 1) };
  }
  if (t < acts.climaxStart - 0.04) {
    return { name: 'EXPLAINER', num: 3, localT: Math.min(Math.max((t - acts.arEnd) / Math.max(acts.climaxStart - acts.arEnd, 0.5), 0), 1) };
  }
  return { name: 'CLIMAX', num: 4, localT: Math.min(Math.max((t - acts.climaxStart) / Math.max(acts.total - acts.climaxStart, 0.5), 0), 1) };
}

function _drawHookPill(ctx, text, y, sc, bg, fg) {
  ctx.save();
  ctx.font = `900 ${14 * sc}px 'Segoe UI', sans-serif`;
  const tw = Math.max(150 * sc, ctx.measureText(text).width + 34 * sc);
  ctx.fillStyle = bg;
  ctx.beginPath();
  ctx.roundRect(-tw * 0.5, y - 15 * sc, tw, 30 * sc, 999);
  ctx.fill();
  ctx.fillStyle = fg;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 0, y + 1 * sc);
  ctx.restore();
}

function drawAct1HookVisual(ctx, kind, cx, cy, scale, lt, t, pal) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.textBaseline = 'alphabetic';
  const sc = scale;
  const warnCol = pal.light ? '#DC2626' : '#F87171';
  const pillBg = pal.light ? '#1E2F42' : 'rgba(15, 23, 42, 0.86)';

  if (kind === 'phone_chaos') {
    // Glowing phone with erupting red notification bubbles + draining battery bar!
    const shake = Math.sin(t * 28) * 3.5 * sc;
    ctx.save();
    ctx.translate(shake, -10 * sc);
    ctx.fillStyle = pal.light ? '#1E2F42' : '#0F172A';
    ctx.strokeStyle = pal.accent;
    ctx.lineWidth = 3.2 * sc;
    ctx.beginPath();
    ctx.roundRect(-62 * sc, -102 * sc, 124 * sc, 204 * sc, 20 * sc);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#1E293B';
    ctx.beginPath();
    ctx.roundRect(-52 * sc, -86 * sc, 104 * sc, 168 * sc, 12 * sc);
    ctx.fill();
    for (let i = 0; i < 4; i++) {
      const pop = Math.min(Math.max((lt * 3.2 - i * 0.35 + 0.35), 0), 1);
      if (pop <= 0) continue;
      const y = -70 * sc + i * 36 * sc;
      ctx.fillStyle = i % 2 === 0 ? 'rgba(239,68,68,0.92)' : 'rgba(245,158,11,0.92)';
      ctx.beginPath();
      ctx.roundRect(-44 * sc, y, 88 * sc * pop, 24 * sc, 7 * sc);
      ctx.fill();
    }
    ctx.restore();
    for (let i = 0; i < 5; i++) {
      const ang = (i / 5) * Math.PI * 2 + t * 1.4;
      const rx = Math.cos(ang) * 112 * sc;
      const ry = Math.sin(ang) * 72 * sc - 10 * sc;
      ctx.fillStyle = '#EF4444';
      ctx.beginPath();
      ctx.arc(rx, ry, (13 + Math.sin(t * 6 + i) * 2) * sc, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#FFF';
      ctx.font = `900 ${14 * sc}px 'Segoe UI', sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('!', rx, ry + 1);
    }
    const pct = Math.max(18, Math.round(92 - lt * 68));
    ctx.fillStyle = pillBg;
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 2.2 * sc;
    ctx.beginPath();
    ctx.roundRect(-98 * sc, 114 * sc, 196 * sc, 30 * sc, 9 * sc);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = pct < 45 ? '#EF4444' : '#F59E0B';
    ctx.beginPath();
    ctx.roundRect(-92 * sc, 119 * sc, (184 * (pct / 100)) * sc, 20 * sc, 5 * sc);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `900 ${13 * sc}px 'Segoe UI', sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(`FOCUS BATTERY: ${pct}%`, 0, 129 * sc);

  } else if (kind === 'anger_heat') {
    for (let r = 0; r < 4; r++) {
      const cyc = (t * 0.9 + r * 0.25) % 1.0;
      ctx.strokeStyle = `rgba(239, 68, 68, ${(1 - cyc) * 0.72})`;
      ctx.lineWidth = 3.2 * sc;
      ctx.beginPath();
      ctx.arc(0, -14 * sc, (28 + cyc * 102) * sc, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.fillStyle = pal.bgCard;
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 3.2 * sc;
    ctx.beginPath();
    ctx.roundRect(-22 * sc, -104 * sc, 44 * sc, 148 * sc, 22 * sc);
    ctx.fill(); ctx.stroke();
    const fillH = (48 + lt * 88) * sc;
    ctx.fillStyle = '#EF4444';
    ctx.beginPath();
    ctx.roundRect(-13 * sc, 38 * sc - fillH, 26 * sc, fillH, 12 * sc);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(0, 52 * sc, 34 * sc, 0, Math.PI * 2);
    ctx.fill();
    _drawHookPill(ctx, '⚡  STRESS SPIKE RISING', 114 * sc, sc, '#DC2626', '#FFFFFF');

  } else if (kind === 'heavy_wall') {
    const w = 290 * sc, h = 158 * sc;
    ctx.fillStyle = pal.bgCard;
    ctx.strokeStyle = pal.border;
    ctx.lineWidth = 2.4 * sc;
    ctx.beginPath();
    ctx.roundRect(-w * 0.5, -h * 0.5, w, h, 18 * sc);
    ctx.fill(); ctx.stroke();
    ctx.strokeStyle = warnCol;
    ctx.lineWidth = 4.8 * sc;
    ctx.beginPath();
    const steps = 40;
    const drawN = Math.max(8, Math.floor(steps * Math.min(lt * 1.15 + 0.2, 1)));
    for (let i = 0; i <= drawN; i++) {
      const u = i / steps;
      const x = -w * 0.42 + u * w * 0.84;
      const y = -h * 0.28 + Math.pow(u, 2.0) * h * 0.56 + Math.sin(u * 14 + t * 4) * 3 * sc;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    _drawHookPill(ctx, '▼  ENERGY CRASHING', h * 0.5 + 24 * sc, sc, '#DC2626', '#FFFFFF');

  } else if (kind === 'rushing_calendar') {
    const flipPhase = (t * 4.2) % 1.0;
    ctx.fillStyle = '#F7F3E6';
    ctx.strokeStyle = '#1E2F42';
    ctx.lineWidth = 3.2 * sc;
    ctx.beginPath();
    ctx.roundRect(-88 * sc, -92 * sc, 176 * sc, 178 * sc, 16 * sc);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#DC2626';
    ctx.beginPath();
    ctx.roundRect(-88 * sc, -92 * sc, 176 * sc, 46 * sc, [16 * sc, 16 * sc, 0, 0]);
    ctx.fill();
    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
    const dIdx = lt > 0.65 ? 4 : Math.floor(t * 5) % 5;
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `900 ${15 * sc}px 'Segoe UI', sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('NONSTOP WEEK', 0, -69 * sc);
    ctx.fillStyle = dIdx === 4 ? '#0F766E' : '#1E2F42';
    ctx.font = `900 ${48 * sc}px 'Segoe UI', sans-serif`;
    ctx.fillText(days[dIdx], 0, 14 * sc);
    ctx.fillStyle = `rgba(15,23,42,${0.16 * Math.sin(flipPhase * Math.PI)})`;
    ctx.fillRect(-85 * sc, -45 * sc, 170 * sc, 128 * sc * flipPhase);
    _drawHookPill(ctx, dIdx === 4 ? '✦  STOP & RESET TODAY' : '⏳  DAYS BLURRING PAST', 112 * sc, sc, pillBg, '#FDE68A');

  } else if (kind === 'comparison_scroll') {
    for (let i = 0; i < 3; i++) {
      const yOff = (((i * 82) - t * 62) % 230 + 230) % 230 - 115;
      ctx.fillStyle = pal.bgCard;
      ctx.strokeStyle = i === 1 ? '#F59E0B' : pal.border;
      ctx.lineWidth = 2.2 * sc;
      ctx.beginPath();
      ctx.roundRect(-114 * sc, yOff * sc, 228 * sc, 60 * sc, 12 * sc);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = pal.accent;
      ctx.beginPath(); ctx.arc(-82 * sc, (yOff + 30) * sc, 14 * sc, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = pal.muted;
      ctx.fillRect(-56 * sc, (yOff + 16) * sc, 142 * sc, 10 * sc);
      ctx.fillRect(-56 * sc, (yOff + 34) * sc, 94 * sc, 8 * sc);
    }
    _drawHookPill(ctx, 'ENDLESS COMPARISON FEED', 124 * sc, sc, '#DC2626', '#FFFFFF');

  } else if (kind === 'needle_ocean') {
    const tipY = -6 * sc + Math.sin(t * 2) * 6 * sc;
    ctx.fillStyle = '#E2E8F0';
    ctx.beginPath();
    ctx.moveTo(-9 * sc, -108 * sc); ctx.lineTo(9 * sc, -108 * sc);
    ctx.lineTo(0, tipY); ctx.closePath(); ctx.fill();
    const g = ctx.createRadialGradient(0, tipY + 26 * sc, 2, 0, tipY + 26 * sc, 48 * sc);
    g.addColorStop(0, 'rgba(255,250,220,0.95)'); g.addColorStop(1, 'rgba(255,250,220,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(0, tipY + 26 * sc, 48 * sc, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#FFFDF5';
    ctx.beginPath(); ctx.arc(0, tipY + 26 * sc, 16 * sc, 0, Math.PI * 2); ctx.fill();
    _drawHookPill(ctx, '1 DROP  VS  ENDLESS OCEAN', 110 * sc, sc, pillBg, '#FDE68A');

  } else {
    // 'racing_mind' — jagged crimson stress waves + spinning thought rings!
    for (let ring = 0; ring < 3; ring++) {
      ctx.save();
      ctx.rotate(t * (ring % 2 === 0 ? 1.15 : -0.85) + ring);
      ctx.strokeStyle = ring === 0 ? 'rgba(248,113,113,0.82)' : 'rgba(251,191,36,0.52)';
      ctx.lineWidth = 2.8 * sc;
      ctx.setLineDash([14 * sc, 10 * sc]);
      ctx.beginPath();
      ctx.arc(0, -8 * sc, (54 + ring * 25) * sc, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
    ctx.strokeStyle = warnCol;
    ctx.lineWidth = 3.6 * sc;
    ctx.beginPath();
    for (let i = 0; i <= 36; i++) {
      const u = i / 36;
      const x = (-72 + u * 144) * sc;
      const amp = Math.sin(u * Math.PI) * 32 * sc;
      const y = -8 * sc + Math.sin(u * 24 + t * 11) * amp;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    _drawHookPill(ctx, 'OVERTHINKING LOOP ACTIVE', 120 * sc, sc, '#DC2626', '#FFFFFF');
  }
  ctx.restore();
}

function drawAct3ExplainerVisual(ctx, actsCfg, cx, cy, scale, lt, t, pal) {
  const kind = (actsCfg && actsCfg.explainer_visual) || 'brain_wave_calm';
  ctx.save();
  ctx.translate(cx, cy);
  ctx.textBaseline = 'alphabetic';
  const sc = scale;
  const cardW = 550 * sc, cardH = 308 * sc;
  const warnText = pal.light ? '#B91C1C' : '#FCA5A5';
  const goodText = pal.light ? '#047857' : '#A7F3D0';

  // Clean themed explainer card frame
  ctx.fillStyle = pal.bgCard;
  ctx.strokeStyle = pal.border;
  ctx.lineWidth = 2.5 * sc;
  ctx.beginPath();
  ctx.roundRect(-cardW * 0.5, -cardH * 0.5, cardW, cardH, 22 * sc);
  ctx.fill(); ctx.stroke();

  // Top label bar inside explainer card
  ctx.fillStyle = pal.accent;
  ctx.font = `900 ${15 * sc}px 'Segoe UI', sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText('✦  HOW IT WORKS IN YOUR MIND  ✦', 0, -cardH * 0.5 + 32 * sc);

  if (kind === 'brain_wave_calm') {
    const calmBlend = Math.min(Math.max((lt - 0.10) / 0.60, 0), 1);
    const waveW = cardW * 0.82;
    ctx.strokeStyle = pal.light ? 'rgba(30,47,66,0.16)' : 'rgba(255,255,255,0.14)';
    ctx.lineWidth = 1.5 * sc;
    ctx.beginPath(); ctx.moveTo(-waveW * 0.5, -14 * sc); ctx.lineTo(waveW * 0.5, -14 * sc); ctx.stroke();

    const rC = Math.round(239 + (16 - 239) * calmBlend);
    const gC = Math.round(68 + (185 - 68) * calmBlend);
    const bC = Math.round(68 + (129 - 68) * calmBlend);
    ctx.strokeStyle = `rgb(${rC},${gC},${bC})`;
    ctx.lineWidth = 4.5 * sc;
    ctx.beginPath();
    for (let i = 0; i <= 80; i++) {
      const u = i / 80;
      const x = -waveW * 0.5 + u * waveW;
      const panicY = Math.sin(u * 42 + t * 10) * 44 * sc * Math.sin(u * Math.PI);
      const calmY = Math.sin(u * 10 + t * 2.5) * 18 * sc * Math.sin(u * Math.PI);
      const y = -14 * sc + panicY * (1 - calmBlend) + calmY * calmBlend;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.font = `800 ${15 * sc}px 'Segoe UI', sans-serif`;
    ctx.fillStyle = calmBlend < 0.5 ? warnText : pal.muted;
    ctx.textAlign = 'left';
    ctx.fillText('✕  ' + (actsCfg.before_label || '').slice(0, 30), -waveW * 0.5, 62 * sc);
    ctx.fillStyle = calmBlend >= 0.35 ? goodText : pal.muted;
    ctx.textAlign = 'right';
    ctx.fillText('✓  ' + (actsCfg.after_label || '').slice(0, 30), waveW * 0.5, 92 * sc);

  } else if (kind === 'focus_battery_charge') {
    const pct = Math.round(24 + Math.min(lt * 1.15, 1) * 71);
    const bw = 330 * sc, bh = 84 * sc;
    ctx.strokeStyle = pal.accent;
    ctx.lineWidth = 3.5 * sc;
    ctx.beginPath();
    ctx.roundRect(-bw * 0.5, -56 * sc, bw, bh, 16 * sc);
    ctx.stroke();
    ctx.fillStyle = pal.accent;
    ctx.beginPath();
    ctx.roundRect(bw * 0.5 + 4 * sc, -32 * sc, 12 * sc, 36 * sc, 4 * sc);
    ctx.fill();
    ctx.fillStyle = pct < 45 ? '#F59E0B' : pal.good;
    ctx.beginPath();
    ctx.roundRect(-bw * 0.5 + 8 * sc, -48 * sc, ((bw - 16 * sc) * (pct / 100)), bh - 16 * sc, 10 * sc);
    ctx.fill();
    ctx.fillStyle = pal.light ? '#1E2F42' : '#FFFFFF';
    ctx.font = `900 ${32 * sc}px 'Segoe UI', sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(`${pct}% CLARITY`, 0, 0);
    ctx.fillStyle = goodText;
    ctx.font = `800 ${17 * sc}px 'Segoe UI', sans-serif`;
    ctx.fillText('✓  ' + (actsCfg.after_label || ''), 0, 68 * sc);

  } else if (kind === 'one_third_pie') {
    const r = 74 * sc;
    const segs = [
      { col: '#F59E0B', lbl: '1/3 FOOD',   a0: -Math.PI/2, a1: -Math.PI/2 + Math.PI*2/3 },
      { col: '#38BDF8', lbl: '1/3 WATER',  a0: -Math.PI/2 + Math.PI*2/3, a1: -Math.PI/2 + Math.PI*4/3 },
      { col: '#10B981', lbl: '1/3 BREATH', a0: -Math.PI/2 + Math.PI*4/3, a1: -Math.PI/2 + Math.PI*2 },
    ];
    segs.forEach((sg, i) => {
      const reveal = Math.min(Math.max(lt * 2.8 - i * 0.65 + 0.3, 0), 1);
      if (reveal <= 0) return;
      ctx.fillStyle = sg.col;
      ctx.beginPath();
      ctx.moveTo(-92 * sc, 2 * sc);
      ctx.arc(-92 * sc, 2 * sc, r, sg.a0, sg.a0 + (sg.a1 - sg.a0) * reveal);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = sg.col;
      ctx.fillRect(16 * sc, (-42 + i * 38) * sc, 16 * sc, 16 * sc);
      ctx.fillStyle = pal.ink;
      ctx.font = `800 ${18 * sc}px 'Segoe UI', sans-serif`;
      ctx.textAlign = 'left';
      ctx.fillText(sg.lbl, 42 * sc, (-28 + i * 38) * sc);
    });

  } else if (kind === 'posture_cool_down') {
    const cool = Math.min(Math.max((lt - 0.12) / 0.65, 0), 1);
    const barMax = 370 * sc;
    ctx.fillStyle = warnText;
    ctx.font = `800 ${15 * sc}px 'Segoe UI', sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText('STANDING (STRESS SURGE)', -barMax * 0.5, -52 * sc);
    ctx.fillStyle = 'rgba(239,68,68,0.22)';
    ctx.beginPath(); ctx.roundRect(-barMax * 0.5, -42 * sc, barMax, 24 * sc, 8 * sc); ctx.fill();
    ctx.fillStyle = '#EF4444';
    ctx.beginPath(); ctx.roundRect(-barMax * 0.5, -42 * sc, barMax * (0.92 - cool * 0.58), 24 * sc, 8 * sc); ctx.fill();

    ctx.fillStyle = goodText;
    ctx.fillText('SITTING DOWN (CALM CONTROL)', -barMax * 0.5, 22 * sc);
    ctx.fillStyle = 'rgba(16,185,129,0.22)';
    ctx.beginPath(); ctx.roundRect(-barMax * 0.5, 32 * sc, barMax, 24 * sc, 8 * sc); ctx.fill();
    ctx.fillStyle = pal.good;
    ctx.beginPath(); ctx.roundRect(-barMax * 0.5, 32 * sc, barMax * (0.20 + cool * 0.76), 24 * sc, 8 * sc); ctx.fill();

  } else if (kind === 'four_pillar_map') {
    const nodes = [
      { x: 0, y: -62, lbl: 'FAITH' },
      { x: 138, y: 2, lbl: 'WEALTH' },
      { x: 0, y: 68, lbl: 'KNOWLEDGE' },
      { x: -138, y: 2, lbl: 'POWER' },
    ];
    ctx.strokeStyle = pal.border;
    ctx.lineWidth = 2.2 * sc;
    ctx.beginPath();
    ctx.arc(0, 2 * sc, 76 * sc, 0, Math.PI * 2);
    ctx.stroke();
    nodes.forEach((n, i) => {
      const on = (lt * 3.8 + 0.4) >= i;
      ctx.fillStyle = on ? pal.accent : (pal.light ? 'rgba(30,47,66,0.18)' : 'rgba(255,255,255,0.14)');
      ctx.beginPath();
      ctx.roundRect((n.x - 60) * sc, (n.y - 18) * sc, 120 * sc, 34 * sc, 999);
      ctx.fill();
      ctx.fillStyle = on ? '#0B1220' : pal.muted;
      ctx.font = `900 ${14 * sc}px 'Segoe UI', sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(n.lbl, n.x * sc, (n.y + 4) * sc);
    });

  } else {
    const showAfter = Math.min(Math.max((lt - 0.14) / 0.34, 0), 1);
    const rw = cardW * 0.86, rh = 62 * sc;
    ctx.globalAlpha = 1 - showAfter * 0.32;
    ctx.fillStyle = pal.light ? 'rgba(239, 68, 68, 0.14)' : 'rgba(239, 68, 68, 0.18)';
    ctx.strokeStyle = pal.light ? 'rgba(220, 38, 38, 0.65)' : 'rgba(248, 113, 113, 0.65)';
    ctx.lineWidth = 2 * sc;
    ctx.beginPath(); ctx.roundRect(-rw * 0.5, -72 * sc, rw, rh, 14 * sc); ctx.fill(); ctx.stroke();
    ctx.fillStyle = warnText;
    ctx.font = `800 ${18 * sc}px 'Segoe UI', sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('✕   ' + (actsCfg.before_label || ''), 0, -34 * sc);

    ctx.globalAlpha = Math.max(0.20, showAfter);
    const slideY = (1 - showAfter) * 20 * sc;
    ctx.fillStyle = pal.light ? 'rgba(16, 185, 129, 0.20)' : 'rgba(52, 211, 153, 0.18)';
    ctx.strokeStyle = pal.good;
    ctx.lineWidth = 2.6 * sc;
    ctx.beginPath(); ctx.roundRect(-rw * 0.5, 12 * sc + slideY, rw, rh, 14 * sc); ctx.fill(); ctx.stroke();
    ctx.fillStyle = goodText;
    ctx.font = `900 ${19 * sc}px 'Segoe UI', sans-serif`;
    ctx.fillText('✓   ' + (actsCfg.after_label || ''), 0, 50 * sc + slideY);
    ctx.globalAlpha = 1;
  }

  // Crisp bottom takeaway metric pill inside explainer card
  ctx.fillStyle = pal.light ? 'rgba(30,47,66,0.12)' : 'rgba(255,255,255,0.10)';
  ctx.beginPath();
  ctx.roundRect(-cardW * 0.40, cardH * 0.5 - 42 * sc, cardW * 0.80, 28 * sc, 999);
  ctx.fill();
  ctx.fillStyle = pal.light ? '#1E2F42' : pal.accent;
  ctx.font = `900 ${13 * sc}px 'Segoe UI', sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText(actsCfg.stat_badge || '', 0, cardH * 0.5 - 23 * sc);

  ctx.restore();
}
"""

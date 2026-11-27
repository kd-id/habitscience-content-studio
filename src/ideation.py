from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import slugify


DEFAULT_CONTENT_PILLARS: list[dict[str, str]] = [
    {
        "id": "minute_wisdom_dua",
        "label": "Minute Wisdom & Healing Duas",
        "description": "Symbolic nature-transformation stories (fire/stress to rain to blooming meadow) unpacking healing Prophetic Duas & calm emotional resets.",
    },
    {
        "id": "prophetic_habits",
        "label": "Prophetic Habits & Daily Sunnah",
        "description": "Daily Prophetic routines (Fajr Barakah, Qailulah nap, Istiqamah, early sleep, morning Dua) over 5-prayer sky & mosque water reflections.",
    },
    {
        "id": "sunnah_paper_story",
        "label": "Sunnah Craft Stories",
        "description": "Warm pastel 3D paper-cutout diorama explainers bringing beloved Prophetic habits (Jumu'ah, Niyyah, smiling, fasting, focus minimalism) to life.",
    },
    {
        "id": "quran_mental_peace",
        "label": "Qur'an Wisdom & Mental Peace",
        "description": "Contemplative obsidian & 24k gold sunburst visualizer with uncut Syaikh Mishary Alafasy tilawah & word-by-word Arabic/English karaoke.",
    },
    {
        "id": "sunnah_particle_map",
        "label": "Sunnah & Brain Science Map",
        "description": "Cosmic morphing particle constellations unpacking structured Prophetic frameworks (Al-Kahfi 4 trials, 1/3 rule, guarding speech, inner change).",
    },
    {
        "id": "hadith_cinematic_story",
        "label": "Reflective Hadith & Qur'an Metaphors",
        "description": "Atmospheric scene-by-scene cinematic visual metaphors (needle in the ocean, twilight plains, warm sunset clouds) with crisp centered storytelling subtitles.",
    },
]

# 30 human-verified authentic Qur'an & Sahih Hadith topics split cleanly across all 6 locked Format Packages (5 each).
# Every entry carries verified Arabic script with harakat, transliteration, accurate translation, and exact source citation.
PILLAR_TOPIC_BANKS: dict[str, list[dict[str, Any]]] = {
    "minute_wisdom_dua": [
        {
            "topic": "The Prophetic Dua Against Worry, Overthinking, and Feeling Stuck",
            "angle": "Why the Prophet paired worry and grief right beside helplessness and laziness—and how naming them frees your mind",
            "hook": "Ever feel too heavy to start even one simple task? The Prophet taught a short Dua that names the exact four mental weights.",
            "keywords": ["dua", "anxiety", "laziness", "overthinking", "prophetic wisdom"],
            "dalil": {
                "arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ",
                "transliteration": "Allahumma inni a'udhu bika minal-hammi wal-hazan, wal-'ajzi wal-kasal",
                "translation": "O Allah, I seek refuge in You from worry and grief, and from helplessness and laziness.",
                "citation": "SAHIH AL-BUKHARI 6369",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "6369",
                "visual_theme": "nature_transform",
            },
        },
        {
            "topic": "Why the Prophet Told Angry People to Sit Down Right Away (Body-Brain Reset)",
            "angle": "How shifting your physical posture instantly interrupts an anger surge before you say something you regret",
            "hook": "Next time anger spikes inside your chest, don't argue—just sit down. Here is why that Prophetic command cools your brain fast.",
            "keywords": ["anger control", "sunnah", "brain science", "calm", "hadith"],
            "dalil": {
                "arabic": "إِذَا غَضِبَ أَحَدُكُمْ وَهُوَ قَائِمٌ فَلْيَجْلِسْ",
                "transliteration": "Idha ghadiba ahadukum wa huwa qa'imun fal-yajlis",
                "translation": "When one of you becomes angry while standing, let him sit down.",
                "citation": "SUNAN ABI DAWUD 4782",
                "surah_or_book_ar": "سنن أبي داود",
                "badge_num": "4782",
                "visual_theme": "nature_transform",
            },
        },
        {
            "topic": "Why Perfectionism Kills Good Habits—and the Sunnah of Choosing Ease",
            "angle": "How lowering friction and welcoming gentle progress keeps your heart and mind steady for life",
            "hook": "Making your daily routine harsh and extreme isn't discipline—it is the fastest way to quit. Look at the Prophetic balance.",
            "keywords": ["ease", "perfectionism", "sunnah", "habits", "burnout"],
            "dalil": {
                "arabic": "يَسِّرُوا وَلَا تُعَسِّرُوا وَبَشِّرُوا وَلَا تُنَفِّرُوا",
                "transliteration": "Yassiru wa la tu'assiru, wa bashshiru wa la tunaffiru",
                "translation": "Make things easy and do not make them difficult; give glad tidings and do not drive people away.",
                "citation": "SAHIH AL-BUKHARI 69",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "69",
                "visual_theme": "nature_transform",
            },
        },
        {
            "topic": "Why the Prophet Drank Water in 3 Calm Sips (Mindful Hydration Science)",
            "angle": "How pausing to breathe three times while drinking calms your nervous system and resets rushing habits",
            "hook": "Even the way you drink a glass of water can train your mind to slow down—here is the quiet three-sip Sunnah.",
            "keywords": ["drinking water", "sunnah", "mindfulness", "calm", "daily habit"],
            "dalil": {
                "arabic": "كَانَ يَتَنَفَّسُ فِي الشَّرَابِ ثَلَاثًا وَيَقُولُ إِنَّهُ أَرْوَى وَأَبْرَأُ وَأَمْرَأُ",
                "transliteration": "Kana yatanaffasu fish-sharabi thalathan, wa yaqulu: innahu arwa wa abra'u wa amra'",
                "translation": "He would pause and breathe three times while drinking, saying it is more quenching, healthier, and more wholesome.",
                "citation": "SAHIH MUSLIM 2028",
                "surah_or_book_ar": "صحيح مسلم",
                "badge_num": "2028",
                "visual_theme": "nature_transform",
            },
        },
        {
            "topic": "The Prophetic Bedtime Reset That Quiets a Racing Mind at Night",
            "angle": "How surrendering the day with a short bedtime Dua and forgiveness signals safety for deep sleep",
            "hook": "Does your mind suddenly replay every mistake the second your head hits the pillow? Try this quiet Prophetic closing ritual.",
            "keywords": ["bedtime dua", "sleep peace", "sunnah", "racing thoughts", "night routine"],
            "dalil": {
                "arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
                "transliteration": "Bismika Allahumma amutu wa ahya",
                "translation": "In Your name, O Allah, I die and I live.",
                "citation": "SAHIH AL-BUKHARI 6324",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "6324",
                "visual_theme": "nature_transform",
            },
        },
    ],
    "prophetic_habits": [
        {
            "topic": "Why Small Daily Habits Beat Big Bursts of Motivation (Sunnah of Istiqamah)",
            "angle": "How the Prophetic rule of small steady deeds aligns with how your brain actually builds lasting habits",
            "hook": "Ever feel fired up on Monday—then completely burned out by Thursday? The Prophet taught a much wiser rhythm.",
            "keywords": ["sunnah", "istiqamah", "prophetic habits", "consistency", "brain science"],
            "dalil": {
                "arabic": "أَحَبُّ الْأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ",
                "transliteration": "Ahabbul a'mali ilallahi adwamuha wa in qall",
                "translation": "The most beloved deeds to Allah are the most consistent, even if they are small.",
                "citation": "SAHIH AL-BUKHARI 6464",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "6464",
                "visual_theme": "prayer_sky",
            },
        },
        {
            "topic": "Why Waking Up Early Brings Barakah and Unmatched Morning Clarity",
            "angle": "How the Prophetic prayer for early mornings matches your brain's sharpest, quietest focus hours",
            "hook": "Before the notifications start and the world gets noisy, there is a hidden window of peace most people sleep right through.",
            "keywords": ["fajr", "early morning", "barakah", "sunnah", "morning focus"],
            "dalil": {
                "arabic": "اللَّهُمَّ بَارِكْ لِأُمَّتِي فِي بُكُورِهَا",
                "transliteration": "Allahumma barik li-ummati fi bukuriha",
                "translation": "O Allah, bless my nation in its early mornings.",
                "citation": "SUNAN ABI DAWUD 2606",
                "surah_or_book_ar": "سنن أبي داود",
                "badge_num": "2606",
                "visual_theme": "prayer_sky",
            },
        },
        {
            "topic": "Qailulah: Why a 20-Minute Prophetic Midday Rest Recharges Your Brain",
            "angle": "The forgotten Sunnah of brief midday rest and why modern sleep science calls it the ultimate afternoon reset",
            "hook": "Hit a heavy wall every afternoon at 2 PM? Long before modern sleep labs, the Sunnah gave us the 20-minute Qailulah reset.",
            "keywords": ["qailulah", "power nap", "sunnah", "afternoon focus", "rest"],
            "dalil": {
                "arabic": "قِيلُوا فَإِنَّ الشَّيَاطِينَ لَا تَقِيلُ",
                "transliteration": "Qilu fa-innash-shayatina la taqil",
                "translation": "Take a brief midday rest, for the devils do not rest at midday.",
                "citation": "SAHIH AL-JAMI' 4431",
                "surah_or_book_ar": "صحيح الجامع",
                "badge_num": "4431",
                "visual_theme": "prayer_sky",
            },
        },
        {
            "topic": "Why Sleeping Early After Isha Heals Your Mind Deeper Than Late Nights",
            "angle": "How honoring night as a peaceful covering restores emotional calm and sharp morning energy",
            "hook": "Staying up scrolling after midnight feels like free time—until it quietly steals tomorrow's peace and clarity.",
            "keywords": ["sleep", "isha", "night routine", "quran", "recovery"],
            "dalil": {
                "arabic": "وَجَعَلْنَا نَوْمَكُمْ سُبَاتًا ۝ وَجَعَلْنَا اللَّيْلَ لِبَاسًا",
                "transliteration": "Wa ja'alna nawmakum subata, wa ja'alnal-layla libasa",
                "translation": "And We made your sleep a means for rest, and made the night a covering.",
                "citation": "QUR'AN 78:9-10",
                "surah_or_book_ar": "سورة النبأ",
                "badge_num": "78:9",
                "visual_theme": "prayer_sky",
            },
        },
        {
            "topic": "The 10-Second Morning Dua That Programs Your Brain for Meaningful Work",
            "angle": "How asking for beneficial knowledge, pure provision, and accepted deeds filters out daily noise",
            "hook": "Most people start the day checking someone else's chaos. Imagine starting with three quiet words that align your entire day.",
            "keywords": ["morning dua", "prophetic habit", "focus", "intention", "sunnah"],
            "dalil": {
                "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا طَيِّبًا وَعَمَلًا مُتَقَبَّلًا",
                "transliteration": "Allahumma inni as'aluka 'ilman nafi'a, wa rizqan tayyiba, wa 'amalan mutaqabbala",
                "translation": "O Allah, I ask You for beneficial knowledge, pure provision, and accepted deeds.",
                "citation": "SUNAN IBN MAJAH 925",
                "surah_or_book_ar": "سنن ابن ماجه",
                "badge_num": "925",
                "visual_theme": "prayer_sky",
            },
        },
    ],
    "sunnah_paper_story": [
        {
            "topic": "Why Friday (Jumu'ah) Is Designed as Your Weekly Spiritual and Mental Reset",
            "angle": "How stepping away from the grind for reflection, Salawat, and community refreshes your heart and focus",
            "hook": "Every seven days, you are invited to pause the noise, wash away the week's heaviness, and renew your heart on the best day of the week.",
            "keywords": ["friday", "jumuah", "sunnah", "weekly reset", "peace"],
            "dalil": {
                "arabic": "خَيْرُ يَوْمٍ طَلَعَتْ عَلَيْهِ الشَّمْسُ يَوْمُ الْجُمُعَةِ",
                "transliteration": "Khayru yawmin tala'at 'alayhish-shamsu yawmul-Jumu'ah",
                "translation": "The best day on which the sun has risen is Friday.",
                "citation": "SAHIH MUSLIM 854",
                "surah_or_book_ar": "صحيح مسلم",
                "badge_num": "JUMU'AH",
            },
        },
        {
            "topic": "Niyyah: The 3-Second Prophetic Pause That Breaks Autopilot Living",
            "angle": "How setting a pure intention before you work turns ordinary effort into focused worship and deep purpose",
            "hook": "Do you ever finish a busy day and wonder where the hours went? A three-second pause called Niyyah changes everything.",
            "keywords": ["niyyah", "intention", "hadith", "focus", "purpose"],
            "dalil": {
                "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
                "transliteration": "Innamal-a'malu bin-niyyat",
                "translation": "Actions are judged only by their intentions.",
                "citation": "SAHIH AL-BUKHARI 1",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "NIYYAH",
            },
        },
        {
            "topic": "Why One Genuine Smile Is Charity—and Calms Two Nervous Systems at Once",
            "angle": "How the Sunnah of warmth and smiling eases hidden tension and lifts both your mood and others'",
            "hook": "Charity doesn't always require money. A single sincere smile softens stress in your own brain and in the person across from you.",
            "keywords": ["smiling", "sunnah", "charity", "kindness", "brain science"],
            "dalil": {
                "arabic": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
                "transliteration": "Tabassumuka fi wajhi akhika laka sadaqah",
                "translation": "Your smile in the face of your brother is an act of charity.",
                "citation": "JAMI' AT-TIRMIDHI 1956",
                "surah_or_book_ar": "جامع الترمذي",
                "badge_num": "SADAQAH",
            },
        },
        {
            "topic": "Monday and Thursday Fasting: What Gentle Fasting Does to Your Mental Clarity",
            "angle": "How the Prophetic twice-weekly fasting rhythm steadies energy, trains self-control, and clears mental fog",
            "hook": "Why do so many people feel sharper and calmer on fasting days? Look at the centuries-old Monday and Thursday Sunnah.",
            "keywords": ["monday thursday fasting", "sunnah fasting", "mental clarity", "self control", "science"],
            "dalil": {
                "arabic": "تُعْرَضُ الْأَعْمَالُ يَوْمَ الِاثْنَيْنِ وَالْخَمِيسِ فَأُحِبُّ أَنْ يُعْرَضَ عَمَلِي وَأَنَا صَائِمٌ",
                "transliteration": "Tu'radul-a'malu yawmal-ithnayni wal-khamis, fa-uhibbu an yu'rada 'amali wa ana sa'im",
                "translation": "Deeds are presented on Mondays and Thursdays, and I love for my deeds to be presented while I am fasting.",
                "citation": "JAMI' AT-TIRMIDHI 747",
                "surah_or_book_ar": "جامع الترمذي",
                "badge_num": "MON & THU",
            },
        },
        {
            "topic": "Leaving What Doesn't Concern You: The Original Prophetic Focus Rule",
            "angle": "How dropping internet drama and pointless distractions frees up hours of peaceful clarity",
            "hook": "Most stress today comes from problems that don't even belong to your life. This short Hadith is the ultimate minimalist focus rule.",
            "keywords": ["minimalism", "focus", "distraction", "hadith", "peace of mind"],
            "dalil": {
                "arabic": "مِنْ حُسْنِ إِسْلَامِ الْمَرْءِ تَرْكُهُ مَا لَا يَعْنِيهِ",
                "transliteration": "Min husni islamil-mar'i tarkuhu ma la ya'nih",
                "translation": "Part of the perfection of a person's Islam is leaving alone that which does not concern him.",
                "citation": "JAMI' AT-TIRMIDHI 2317",
                "surah_or_book_ar": "جامع الترمذي",
                "badge_num": "FOCUS",
            },
        },
    ],
    "quran_mental_peace": [
        {
            "topic": "Why Your Mind Stays Restless Until It Remembers Allah (Surah Ar-Ra'd 13:28)",
            "angle": "How quiet rhythmic Dhikr settles racing thoughts and lowers your brain's nonstop stress loop",
            "hook": "You can turn off every notification and still feel loud inside. Surah Ar-Ra'd points directly to what actually quiets the heart.",
            "keywords": ["surah ar rad", "dhikr", "mental peace", "quran", "calm mind"],
            "dalil": {
                "arabic": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
                "transliteration": "Ala bi-dhikrillahi tatma'innul-qulub",
                "translation": "Verily, in the remembrance of Allah do hearts find rest.",
                "citation": "QUR'AN 13:28",
                "surah_or_book_ar": "سورة الرعد",
                "badge_num": "28",
                "visual_theme": "gold_obsidian",
            },
        },
        {
            "topic": "Why the Qur'an Says Relief Comes WITH Hardship, Not Just After (94:5-6)",
            "angle": "A tiny word in Surah Ash-Sharh that shifts a panicked brain into calm, hopeful clarity",
            "hook": "Read Surah Ash-Sharh slowly: it does not say ease comes only after hardship—it says ease is already WITH hardship.",
            "keywords": ["surah ash sharh", "hardship", "ease", "hope", "quran peace"],
            "dalil": {
                "arabic": "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ۝ إِنَّ مَعَ الْعُسْرِ يُسْرًا",
                "transliteration": "Fa-inna ma'al-'usri yusra, inna ma'al-'usri yusra",
                "translation": "For indeed, with hardship comes ease. Indeed, with hardship comes ease.",
                "citation": "QUR'AN 94:5-6",
                "surah_or_book_ar": "سورة الشرح",
                "badge_num": "94:5",
                "visual_theme": "gold_obsidian",
            },
        },
        {
            "topic": "The Science of Shukr: How Gratitude Rewires a Stressed Brain (Surah Ibrahim 14:7)",
            "angle": "Why authentic gratitude interrupts worry loops and trains your attention to notice hidden blessings",
            "hook": "Your brain is wired to hunt for what is missing—until one daily habit from Surah Ibrahim flips the entire switch.",
            "keywords": ["shukr", "gratitude", "surah ibrahim", "brain science", "happiness"],
            "dalil": {
                "arabic": "لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ",
                "transliteration": "La'in shakartum la-azidannakum",
                "translation": "If you are grateful, I will surely increase you in favor.",
                "citation": "QUR'AN 14:7",
                "surah_or_book_ar": "سورة إبراهيم",
                "badge_num": "14:7",
                "visual_theme": "gold_obsidian",
            },
        },
        {
            "topic": "How Five Brief Prayer Pauses Reset Daily Stress Before Burnout Hits (2:153)",
            "angle": "Why stepping away five times a day for Sabr and Salah interrupts stress hormones naturally",
            "hook": "What if burnout happens because you never step off the treadmill all day? Look at the built-in rhythm of Salah and patience.",
            "keywords": ["sabr", "salah", "burnout", "stress reset", "quran"],
            "dalil": {
                "arabic": "اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
                "transliteration": "Ista'inu bis-sabri was-salah, innallaha ma'as-sabirin",
                "translation": "Seek help through patience and prayer. Indeed, Allah is with the patient.",
                "citation": "QUR'AN 2:153",
                "surah_or_book_ar": "سورة البقرة",
                "badge_num": "2:153",
                "visual_theme": "gold_obsidian",
            },
        },
        {
            "topic": "Why Not a Single Tiny Good Step Is Ever Wasted (Surah Az-Zalzalah 99:7)",
            "angle": "How honoring even an atom's weight of daily effort builds unstoppable quiet confidence",
            "hook": "Think one small good deed or five quiet minutes doesn't matter? The Qur'an promises not even an atom's weight is ever lost.",
            "keywords": ["small deeds", "consistency", "quran", "habit science", "hope"],
            "dalil": {
                "arabic": "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُ",
                "transliteration": "Fa-man ya'mal mithqala dharratin khayran yarah",
                "translation": "So whoever does an atom's weight of good will see it.",
                "citation": "QUR'AN 99:7",
                "surah_or_book_ar": "سورة الزلزلة",
                "badge_num": "99:7",
                "visual_theme": "gold_obsidian",
            },
        },
    ],
    "sunnah_particle_map": [
        {
            "topic": "Why Reading Surah Al-Kahf Every Friday Guards Your Mind From 4 Modern Traps",
            "angle": "A weekly mental compass against the 4 timeless trials of faith, wealth, pride in knowledge, and power",
            "hook": "Ever wonder why the Prophet encouraged Surah Al-Kahf every single Friday? Its four stories map the exact four traps of modern life.",
            "keywords": ["surah al kahf", "friday sunnah", "four trials", "wisdom", "mindset"],
            "dalil": {
                "arabic": "مَنْ قَرَأَ سُورَةَ الْكَهْفِ فِي يَوْمِ الْجُمُعَةِ أَضَاءَ لَهُ مِنَ النُّورِ مَا بَيْنَ الْجُمُعَتَيْنِ",
                "transliteration": "Man qara'a suratal-Kahfi fi yawmil-Jumu'ati ada'a lahu minan-nuri ma baynal-Jumu'atayn",
                "translation": "Whoever reads Surah Al-Kahf on Friday will have a light shining for him between the two Fridays.",
                "citation": "SAHIH AL-JAMI' 6470",
                "surah_or_book_ar": "صحيح الجامع",
                "badge_num": "6470",
                "particle_shapes": ["crescent_stars", "cave_arch", "balance_scale", "summary_constellation"],
            },
        },
        {
            "topic": "The Prophetic 1/3 Stomach Rule: Why Overeating Causes Instant Brain Fog",
            "angle": "How leaving one-third of your stomach for breath prevents post-lunch crashes and sharpens focus",
            "hook": "Ever feel completely foggy right after a heavy meal? Fourteen hundred years ago, the Prophet gave us the exact 1/3 balance rule.",
            "keywords": ["one third rule", "sunnah eating", "brain fog", "focus", "hadith"],
            "dalil": {
                "arabic": "ثُلُثٌ لِطَعَامِهِ وَثُلُثٌ لِشَرَابِهِ وَثُلُثٌ لِنَفَسِهِ",
                "transliteration": "Thuluthun li-ta'amihi, wa thuluthun li-sharabihi, wa thuluthun li-nafasih",
                "translation": "One third for food, one third for water, and one third for breath.",
                "citation": "JAMI' AT-TIRMIDHI 2380",
                "surah_or_book_ar": "جامع الترمذي",
                "badge_num": "2380",
                "particle_shapes": ["crescent_stars", "balance_scale", "brain_light", "summary_constellation"],
            },
        },
        {
            "topic": "Why Real Life Change Always Starts Inside Your Daily Habits (Ar-Ra'd 13:11)",
            "angle": "How the Qur'anic law of inner change matches modern habit psychology step for step",
            "hook": "Waiting for circumstances to change first keeps you stuck for years. Surah Ar-Ra'd reveals where every real shift starts.",
            "keywords": ["inner change", "habits", "self improvement", "quran", "mindset"],
            "dalil": {
                "arabic": "إِنَّ اللَّهَ لَا يُغَيِّرُ مَا بِقَوْمٍ حَتَّىٰ يُغَيِّرُوا مَا بِأَنفُسِهِمْ",
                "transliteration": "Innallaha la yughayyiru ma bi-qawmin hatta yughayyiru ma bi-anfusihim",
                "translation": "Indeed, Allah will not change the condition of a people until they change what is in themselves.",
                "citation": "QUR'AN 13:11",
                "surah_or_book_ar": "سورة الرعد",
                "badge_num": "13:11",
                "particle_shapes": ["crescent_stars", "brain_light", "sunrise_horizon", "summary_constellation"],
            },
        },
        {
            "topic": "Speak Good or Stay Quiet: Why Guarding Your Words Sharpens Your Mind",
            "angle": "How stepping back from reactive chatter and gossip preserves emotional calm and deep focus",
            "hook": "We talk and comment more than any generation in history—yet feel more drained than ever. Listen to this two-option Prophetic filter.",
            "keywords": ["silence", "speak good", "focus", "sahih bukhari", "mindfulness"],
            "dalil": {
                "arabic": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
                "transliteration": "Man kana yu'minu billahi wal-yawmil-akhiri fal-yaqul khayran aw li-yasmut",
                "translation": "Whoever believes in Allah and the Last Day, let him speak good or remain silent.",
                "citation": "SAHIH AL-BUKHARI 6018",
                "surah_or_book_ar": "صحيح البخاري",
                "badge_num": "6018",
                "particle_shapes": ["crescent_stars", "ocean_drop", "brain_light", "summary_constellation"],
            },
        },
        {
            "topic": "The Prophetic Cure for Social Media Comparison Fatigue (Sahih Muslim 2963)",
            "angle": "Why looking at those who have less instead of scrolling highlight reels restores contentment fast",
            "hook": "Five minutes of scrolling someone else's highlight reel can make a good life feel small. The Prophet gave us the exact antidote.",
            "keywords": ["comparison", "contentment", "gratitude", "sahih muslim", "mental health"],
            "dalil": {
                "arabic": "انْظُرُوا إِلَى مَنْ أَسْفَلَ مِنْكُمْ وَلَا تَنْظُرُوا إِلَى مَنْ هُوَ فَوْقَكُمْ",
                "transliteration": "Unzuru ila man asfala minkum wa la tanzuru ila man huwa fawqakum",
                "translation": "Look at those who have less than you, and do not look at those who have more than you.",
                "citation": "SAHIH MUSLIM 2963",
                "surah_or_book_ar": "صحيح مسلم",
                "badge_num": "2963",
                "particle_shapes": ["crescent_stars", "balance_scale", "sunrise_horizon", "summary_constellation"],
            },
        },
    ],
    "hadith_cinematic_story": [
        {
            "topic": "A Needle in the Ocean: Why We Should Never Make Small Duas (Hadith Qudsi)",
            "angle": "How the ocean metaphor in Sahih Muslim breaks scarcity thinking and expands hope and courage",
            "hook": "Picture dipping a single sewing needle into the entire ocean. That is the Hadith Qudsi that changes how you think about asking Allah.",
            "keywords": ["hadith qudsi", "big dua", "abundance", "sahih muslim", "mindset"],
            "dalil": {
                "arabic": "مَا نَقَصَ ذَلِكَ مِمَّا عِنْدِي إِلَّا كَمَا يَنْقُصُ الْمِخْيَطُ إِذَا أُدْخِلَ الْبَحْرَ",
                "transliteration": "Ma naqasa dhalika mimma 'indi illa kama yanqusul-mikhyatu idha udkhilal-bahr",
                "translation": "That would not decrease what I possess any more than a needle decreases the ocean when dipped into it.",
                "citation": "SAHIH MUSLIM 2577",
                "surah_or_book_ar": "صحيح مسلم",
                "badge_num": "2577",
            },
        },
        {
            "topic": "Tawakkul: Why Releasing Outcomes Frees Up Massive Mental Energy (65:3)",
            "angle": "How doing your honest best and trusting Allah with results stops overthinking dead in its tracks",
            "hook": "Half of your mental exhaustion doesn't come from hard work—it comes from trying to control outcomes you don't own.",
            "keywords": ["tawakkul", "trust in allah", "overthinking", "peace", "quran"],
            "dalil": {
                "arabic": "وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ",
                "transliteration": "Wa man yatawakkal 'alallahi fahuwa hasbuh",
                "translation": "And whoever relies upon Allah — then He is sufficient for him.",
                "citation": "QUR'AN 65:3",
                "surah_or_book_ar": "سورة الطلاق",
                "badge_num": "65:3",
            },
        },
        {
            "topic": "The 4-Word Qur'anic Anchor That Stops Spiraling Anxiety (Ali 'Imran 3:173)",
            "angle": "How repeating a grounded phrase of trust interrupts worst-case thoughts and steadies your breathing",
            "hook": "When fear spirals fast, your mind doesn't need ten long arguments—it needs one unshakable anchor from Surah Ali 'Imran.",
            "keywords": ["hasbunallah", "anxiety relief", "quran", "calm mind", "trust"],
            "dalil": {
                "arabic": "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ",
                "transliteration": "Hasbunallahu wa ni'mal-wakil",
                "translation": "Sufficient for us is Allah, and He is the best Disposer of affairs.",
                "citation": "QUR'AN 3:173",
                "surah_or_book_ar": "سورة آل عمران",
                "badge_num": "3:173",
            },
        },
        {
            "topic": "When Life Feels Too Heavy: The Promise of Surah Al-Baqarah 2:286",
            "angle": "How remembering you already carry the strength for today restores steady problem-solving calm",
            "hook": "On the days you whisper 'I can't handle this anymore,' remember this exact reassurance from the closing of Surah Al-Baqarah.",
            "keywords": ["al baqarah 286", "resilience", "mental strength", "quran", "calm"],
            "dalil": {
                "arabic": "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا",
                "transliteration": "La yukallifullahu nafsan illa wus'aha",
                "translation": "Allah does not burden a soul beyond that it can bear.",
                "citation": "QUR'AN 2:286",
                "surah_or_book_ar": "سورة البقرة",
                "badge_num": "286",
            },
        },
        {
            "topic": "Why Walking Gently and Skipping Petty Arguments Protects Your Peace (25:63)",
            "angle": "How choosing calm dignity over online and daily outrage preserves massive mental energy",
            "hook": "Every petty argument you walk away from is energy you just saved for what truly matters. Surah Al-Furqan describes this poise.",
            "keywords": ["humility", "peace", "emotional control", "quran", "calm"],
            "dalil": {
                "arabic": "وَعِبَادُ الرَّحْمَٰنِ الَّذِينَ يَمْشُونَ عَلَى الْأَرْضِ هَوْنًا",
                "transliteration": "Wa 'ibadur-Rahmani-lladhina yamshuna 'alal-ardi hawna",
                "translation": "And the servants of the Most Merciful are those who walk upon the earth humbly and gently.",
                "citation": "QUR'AN 25:63",
                "surah_or_book_ar": "سورة الفرقان",
                "badge_num": "25:63",
            },
        },
    ],
}

_ACADEMIC_JARGON_MARKERS: tuple[str, ...] = (
    "coupling",
    "correlates",
    "modulates",
    "modulation",
    "striatal",
    "cortical",
    "prefrontal",
    "dopaminergic",
    "fmri",
    "eeg",
    "meta-analysis",
    "longitudinal",
    "randomized",
    "cohort",
    "pathophysiology",
    "neurogenesis",
    "synaptic",
    "hippocampal",
    "adolescents",
    "children and teens",
    "attention-related networks",
    "executive function",
    "cognitive load",
    "et al",
    "study finds",
    "researchers find",
    "journal of",
)


def _core_topic_tokens(title: str) -> set[str]:
    stop = {
        "why", "how", "the", "your", "you", "what", "does", "do", "is", "are", "of", "to", "in",
        "for", "and", "a", "an", "on", "with", "that", "this", "from", "all", "day", "still",
        "just", "even", "after", "when", "makes", "make", "really", "actually", "brain", "focus",
    }
    return {w for w in slugify(title or "", max_length=120).split("-") if len(w) >= 3 and w not in stop}


def _is_near_duplicate_topic(candidate: str, used_topics: list[str], used_slugs: set[str]) -> bool:
    """Block both exact slug matches AND paraphrased near-duplicates of already-produced videos."""
    if not candidate or not candidate.strip():
        return True
    cand_slug = slugify(candidate)
    if cand_slug in used_slugs:
        return True
    cand_is_p2 = "part 2" in candidate.lower() or "part-2" in cand_slug
    cand_toks = _core_topic_tokens(candidate)
    if len(cand_toks) < 2:
        return False
    for prev in used_topics:
        prev_is_p2 = "part 2" in (prev or "").lower()
        # Allow a genuine Part 2 sequel to reference Part 1's topic (but never duplicate an existing Part 2!)
        if cand_is_p2 != prev_is_p2:
            continue
        prev_toks = _core_topic_tokens(prev)
        if len(prev_toks) < 2:
            continue
        overlap = len(cand_toks & prev_toks)
        smaller = min(len(cand_toks), len(prev_toks))
        if smaller > 0 and (overlap / smaller) >= 0.65:
            return True
    return False


def _looks_academic_jargon(title: str) -> bool:
    low = (title or "").lower()
    if not low.strip():
        return True
    if any(m in low for m in _ACADEMIC_JARGON_MARKERS):
        return True
    # Reject overly dense/long news headlines (> 85 chars)
    if len(title.strip()) > 85:
        return True
    return False


@dataclass
class TopicIdea:
    topic: str
    angle: str
    hook: str
    source: str
    source_url: str = ""
    keywords: list[str] | None = None
    discovered_at: str = ""
    pillar: str = "prophetic_habits"
    pillar_label: str = "Prophetic Habits & Daily Sunnah"
    dalil: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["keywords"] = self.keywords or []
        data["discovered_at"] = data["discovered_at"] or datetime.now(timezone.utc).isoformat()
        return data


def load_history(history_file: Path) -> list[dict[str, Any]]:
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def select_next_pillar(history: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, str]:
    """Rotate deterministically across the 3 content pillars so consecutive runs never collide."""
    configured = (config.get("content_pillars") or {}).get("rotation")
    pillars = configured if isinstance(configured, list) and configured else DEFAULT_CONTENT_PILLARS
    valid = [p for p in pillars if isinstance(p, dict) and p.get("id")]
    if not valid:
        valid = DEFAULT_CONTENT_PILLARS

    # Look at the most recent run's pillar first so we strictly advance to the NEXT pillar
    if history:
        last_pillar = str(history[-1].get("pillar") or "").strip()
        ids = [str(p["id"]) for p in valid]
        if last_pillar in ids:
            nxt_idx = (ids.index(last_pillar) + 1) % len(valid)
            return valid[nxt_idx]

    return valid[len(history) % len(valid)]


def _fetch_google_news_rss(query: str, hl: str = "id", gl: str = "ID", ceid: str = "ID:id", limit: int = 5) -> list[dict[str, str]]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    req = urllib.request.Request(url, headers={"User-Agent": "ContentAutomationStudio/1.0"})
    items: list[dict[str, str]] = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            if title:
                clean_title = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
                items.append({
                    "title": clean_title,
                    "raw_title": title,
                    "url": link,
                    "published": pub_date,
                    "query": query,
                })
    except Exception:
        return []
    return items


def discover_trending_candidates(config: dict[str, Any], limit_per_query: int = 4) -> list[dict[str, str]]:
    trends_cfg = config.get("trends", {})
    queries = trends_cfg.get("queries") or [config.get("channel", {}).get("niche", "AI produktivitas")]
    hl = trends_cfg.get("locale_hl", "id")
    gl = trends_cfg.get("locale_gl", "ID")
    ceid = trends_cfg.get("locale_ceid", "ID:id")

    seen_slugs: set[str] = set()
    candidates: list[dict[str, str]] = []
    for query in queries:
        for item in _fetch_google_news_rss(query, hl=hl, gl=gl, ceid=ceid, limit=limit_per_query):
            s = slugify(item["title"])
            if s not in seen_slugs:
                seen_slugs.add(s)
                candidates.append(item)

    for feed_url in trends_cfg.get("custom_rss_feeds") or []:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "ContentAutomationStudio/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:limit_per_query]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if title:
                    s = slugify(title)
                    if s not in seen_slugs:
                        seen_slugs.add(s)
                        candidates.append({"title": title, "raw_title": title, "url": link, "published": "", "query": feed_url})
        except Exception:
            continue

    return candidates


def _load_analytics_insights(history_file: Path) -> dict[str, Any]:
    ins_file = history_file.parent / "analytics_insights.json"
    if not ins_file.exists():
        return {}
    try:
        return json.loads(ins_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _rank_topic_with_gemini(
    candidates: list[dict[str, str]],
    config: dict[str, Any],
    used_slugs: set[str],
    pillar: dict[str, str],
    winning_patterns: list[str] | None = None,
    used_topics: list[str] | None = None,
) -> TopicIdea | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        channel = config.get("channel", {})
        model = config.get("ai", {}).get("text_model", "gemini-3.8-flash")
        pat_txt = (
            f"\nProven high-view patterns from our channel analytics (prioritize matching these!):\n- "
            + "\n- ".join(winning_patterns[:4])
            + "\n"
            if winning_patterns
            else ""
        )

        lang = channel.get("language", "en")
        pillar_id = pillar.get("id", "focus_habits")
        pillar_label = pillar.get("label", "Everyday Focus & Habits")
        pillar_desc = pillar.get("description", "")

        if lang == "en":
            prompt = (
                f"You are the Viral Content Strategist for '{channel.get('name')}' (audience: everyday viewers worldwide, language: super-simple conversational English).\n"
                f"TODAY'S SCHEDULED CONTENT PILLAR (MUST MATCH THIS PILLAR SO DAILY VIDEOS NEVER COLLIDE):\n"
                f"- Pillar ID: {pillar_id} ({pillar_label})\n"
                f"- Pillar Goal: {pillar_desc}\n\n"
                "PLAIN-ENGLISH CLARITY RULES (CRITICAL — ZERO JARGON):\n"
                "1. NEVER copy an academic study title verbatim (e.g. NEVER write 'Dopamine Supports Coupling of Attention-Related Networks' or 'fMRI reveals...').\n"
                "2. Rewrite or invent 1 crystal-clear, bingeable everyday topic a 14-year-old IMMEDIATELY understands in 2 seconds (max 68 chars).\n"
                "   - Good examples for focus_habits: 'Why Checking Your Phone at 7 AM Ruins Your Focus All Day', 'You Are Not Lazy: Why Starting Simple Tasks Feels Hard'\n"
                "   - Good examples for everyday_science: 'Why Coffee Right After Waking Up Makes You Crash at 2 PM', 'Why You Still Feel Tired After Sleeping 8 Hours'\n"
                "   - Good examples for pov_survival: '72 Hours Without Your Phone: Hour 1 Brain Test', 'You Have 6 Hours Left—One Phone Tap Resets the Clock'\n"
                "3. Strictly FORBID jargon words: coupling, prefrontal, correlates, modulates, cortical, striatal, cognitive load, executive function, adolescents.\n"
                f"4. NEVER repeat or paraphrase ANY of these already-produced videos: {json.dumps((used_topics or [])[-25:], ensure_ascii=False)}\n"
                f"{pat_txt}\n"
                f"Optional inspiration news headlines (ONLY use if you rewrite into plain everyday English matching pillar '{pillar_id}'):\n"
                f"{json.dumps(candidates[:10], ensure_ascii=False, indent=2)}\n\n"
                "Return valid JSON with keys: topic, angle, hook, source_url, keywords (array of 5 simple strings)."
            )
        else:
            prompt = (
                f"Kamu adalah Content Strategist untuk channel '{channel.get('name')}' "
                f"(niche: {channel.get('niche')}, audiens: {channel.get('target_audience')}, bahasa: {lang}).\n"
                f"Pilih 1 topik paling potensial viral dan gampang dipahami dari daftar tren berikut, hindari topik yang sudah dipakai ({sorted(list(used_slugs))[:15]}).\n"
                f"Kandidat tren:\n{json.dumps(candidates[:12], ensure_ascii=False, indent=2)}\n\n"
                "Kembalikan JSON valid dengan keys: topic, angle, hook, source_url, keywords (array 5 string)."
            )
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.65,
            ),
        )
        data = json.loads(resp.text)
        picked_topic = str(data.get("topic") or "").strip()
        if not picked_topic or (lang == "en" and _looks_academic_jargon(picked_topic)):
            print(f"[ideation] Rejected overly academic/empty Gemini topic: {picked_topic!r}; using curated pillar bank.", flush=True)
            return None
        if _is_near_duplicate_topic(picked_topic, used_topics or [], used_slugs):
            print(f"[ideation] Rejected duplicate/paraphrased Gemini topic: {picked_topic!r}; using curated pillar bank.", flush=True)
            return None
        return TopicIdea(
            topic=picked_topic,
            angle=str(data.get("angle") or f"Super-simple everyday breakdown for {pillar_label}").strip(),
            hook=str(data.get("hook") or f"Ever wonder why this happens to your brain? Let's break down {picked_topic}.").strip(),
            source=f"gemini_pillar:{pillar_id}",
            source_url=str(data.get("source_url") or ""),
            keywords=[str(k) for k in (data.get("keywords") or [])][:8],
            discovered_at=datetime.now(timezone.utc).isoformat(),
            pillar=pillar_id,
            pillar_label=pillar_label,
        )
    except Exception:
        return None


def _pick_from_pillar_bank(
    pillar: dict[str, str],
    used_slugs: set[str],
    now_iso: str,
    used_topics: list[str] | None = None,
) -> TopicIdea:
    pillar_id = pillar.get("id", "prophetic_habits")
    pillar_label = pillar.get("label", "Prophetic Habits & Daily Sunnah")
    bank = PILLAR_TOPIC_BANKS.get(pillar_id) or PILLAR_TOPIC_BANKS["prophetic_habits"]
    prev_topics = used_topics or []
    chosen = next((item for item in bank if not _is_near_duplicate_topic(item["topic"], prev_topics, used_slugs)), None)
    if chosen is None:
        # Try any unused topic across other banks before wrapping around
        for alt_bank in PILLAR_TOPIC_BANKS.values():
            chosen = next((item for item in alt_bank if not _is_near_duplicate_topic(item["topic"], prev_topics, used_slugs)), None)
            if chosen is not None:
                break
    if chosen is None:
        chosen = bank[len(used_slugs) % len(bank)]

    return TopicIdea(
        topic=str(chosen["topic"]),
        angle=str(chosen["angle"]),
        hook=str(chosen["hook"]),
        source=f"verified_dalil_pillar:{pillar_id}",
        source_url="",
        keywords=list(chosen.get("keywords") or ["sunnah", "quran", "habits", "brain"]),
        discovered_at=now_iso,
        pillar=pillar_id,
        pillar_label=pillar_label,
        dalil=dict(chosen["dalil"]) if isinstance(chosen.get("dalil"), dict) else None,
    )


def select_topic(
    config: dict[str, Any],
    history_file: Path,
    manual_topic: str | None = None,
    manual_angle: str | None = None,
) -> TopicIdea:
    now_iso = datetime.now(timezone.utc).isoformat()
    channel = config.get("channel", {})
    niche = channel.get("niche", "AI & Produktivitas")
    history = load_history(history_file)
    pillar = select_next_pillar(history, config)
    pillar_id = pillar["id"]
    pillar_label = pillar["label"]

    lang = channel.get("language", "en")
    if manual_topic and manual_topic.strip():
        clean_topic = manual_topic.strip()
        if lang == "en":
            # Attach matching verified dalil if manual topic resembles one in our bank
            matched_dalil = None
            low_manual = clean_topic.lower()
            for _bank in PILLAR_TOPIC_BANKS.values():
                for _item in _bank:
                    if any(kw.lower() in low_manual for kw in (_item.get("keywords") or [])[:2]):
                        matched_dalil = dict(_item["dalil"]) if isinstance(_item.get("dalil"), dict) else None
                        break
                if matched_dalil:
                    break
            return TopicIdea(
                topic=clean_topic,
                angle=(manual_angle or "Reflective breakdown connecting authentic Prophetic/Qur'anic wisdom with simple everyday brain & habit science").strip(),
                hook=f"Pause for thirty seconds—here is the timeless wisdom behind {clean_topic}.",
                source="manual_input",
                keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["sunnah", "quran", "habits"],
                discovered_at=now_iso,
                pillar=pillar_id,
                pillar_label=pillar_label,
                dalil=matched_dalil,
            )
        return TopicIdea(
            topic=clean_topic,
            angle=(manual_angle or f"Blueprint praktis dan strategi eksekusi cepat untuk {channel.get('target_audience', 'kreator')}").strip(),
            hook=f"Masih menghabiskan berjam-jam untuk satu konten? Begini cara kerja {clean_topic} dari ide sampai siap publish!",
            source="manual_input",
            keywords=[w for w in slugify(clean_topic).split("-") if len(w) > 2][:6] + ["automasi", "konten"],
            discovered_at=now_iso,
            pillar=pillar_id,
            pillar_label=pillar_label,
        )

    used_slugs = {item.get("slug", "") for item in history}
    used_topics = [str(item.get("topic") or "") for item in history if item.get("topic")]
    insights = _load_analytics_insights(history_file)

    # Closed-Loop Sequel Engine: every 3rd run, automatically produce a Part 2 / sequel
    # directly extending our #1 most-watched video (once real views exist)!
    sequels = insights.get("recommended_sequels") or []
    if len(history) > 0 and (len(history) % 3 == 0) and int(insights.get("total_views_all_platforms", 0)) > 0:
        for seq in sequels:
            seq_topic = str(seq.get("topic") or "").strip()
            if seq_topic and not _is_near_duplicate_topic(seq_topic, used_topics, used_slugs):
                return TopicIdea(
                    topic=seq_topic,
                    angle=str(seq.get("angle") or f"Direct Part 2 sequel expanding our most-watched {niche} episode").strip(),
                    hook=str(seq.get("hook") or f"Because so many of you watched Part 1, here is what happens next: {seq_topic}").strip(),
                    source="analytics_sequel",
                    source_url="",
                    keywords=[str(k) for k in (seq.get("keywords") or ["part 2", "focus", "habits"])][:8],
                    discovered_at=now_iso,
                    pillar=pillar_id,
                    pillar_label=pillar_label,
                )

    # For verified Islamic + Brain Science pillars: ALWAYS pick an unused topic with human-verified Arabic text,
    # harakat, and authentic Qur'an/Hadith citation from our curated bank first (0% chance of hallucinated dalil!).
    if lang == "en" and pillar_id in PILLAR_TOPIC_BANKS:
        bank = PILLAR_TOPIC_BANKS[pillar_id]
        has_fresh_verified = any(not _is_near_duplicate_topic(item["topic"], used_topics, used_slugs) for item in bank)
        if has_fresh_verified:
            return _pick_from_pillar_bank(pillar, used_slugs, now_iso, used_topics=used_topics)

    candidates = discover_trending_candidates(config)
    fresh = [c for c in candidates if not _is_near_duplicate_topic(c["title"], used_topics, used_slugs)]
    pool = fresh or candidates

    gemini_pick = _rank_topic_with_gemini(
        pool,
        config,
        used_slugs,
        pillar=pillar,
        winning_patterns=insights.get("winning_patterns"),
        used_topics=used_topics,
    )
    if gemini_pick:
        return gemini_pick

    # For English HabitSains: NEVER dump raw academic Google News titles straight into a video!
    # Always select a crisp, zero-jargon, everyday topic from the active rotating pillar bank.
    if lang == "en":
        return _pick_from_pillar_bank(pillar, used_slugs, now_iso, used_topics=used_topics)

    if pool:
        top = pool[0]
        return TopicIdea(
            topic=top["title"],
            angle=f"Analisis tren & cara praktik langsung untuk niche {niche}",
            hook=f"Tren ini sedang ramai dibahas: {top['title']} — dan ini dampaknya buat kreator hari ini!",
            source="google_news_rss",
            source_url=top.get("url", ""),
            keywords=[w for w in slugify(top["title"]).split("-") if len(w) > 2][:6],
            discovered_at=now_iso,
            pillar=pillar_id,
            pillar_label=pillar_label,
        )

    fallback_topics = [
        "Cara Membangun Pabrik Konten AI Otomatis untuk YouTube dan Sosmed",
        "Strategi Repurpose 1 Ide Konten Menjadi 7 Format Siap Publish",
        "Workflow AI Harian Kreator: Dari Riset Tren Sampai Auto-Draft dalam 10 Menit",
    ]
    chosen = next((t for t in fallback_topics if slugify(t) not in used_slugs), fallback_topics[0])
    return TopicIdea(
        topic=chosen,
        angle="Framework end-to-end yang langsung bisa dipraktikkan kreator hari ini",
        hook=f"Satu topik bisa berubah jadi video panjang, Shorts, Reels, TikTok, dan Carousel sekaligus—ini caranya!",
        source="evergreen_fallback",
        keywords=["automasi konten", "youtube ai", "repurpose konten", "sosial media", "produktivitas"],
        discovered_at=now_iso,
        pillar=pillar_id,
        pillar_label=pillar_label,
    )

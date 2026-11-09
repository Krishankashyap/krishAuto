/**
 * sanitize.js - Universal text sanitizer for Hindi/English scene elements:
 * Prevents tofu box characters (\uFFFD, \u25A0-\u25FF) and unrendered emojis.
 */

export function sanitizeSceneText(text) {
  if (!text || typeof text !== "string") return "";
  return text
    .normalize("NFC") // Keep Devanagari matras combined with base consonants
    .replace(/[\uFFFD\u25A0-\u25FF\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "") // Strip tofu boxes, symbols & emojis
    .replace(/[^\p{L}\p{N}\p{M}\p{P}\p{Zs}]/gu, "") // Allow only valid letters, combining marks, numbers, punctuation, spaces
    .replace(/\s+/g, " ")
    .trim();
}

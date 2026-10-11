// Country centroids for map placement (event jitter + transfer lines).
// Keyed by ISO2 and by common SIPRI country-name spellings (lowercased).
export const CENTROIDS: Record<string, [number, number]> = {
  SD: [30.2, 15.6], TD: [18.7, 15.4], SS: [30.3, 7.3], CD: [23.7, -2.9], HT: [-72.7, 18.9],
};

export const NAME_CENTROIDS: Record<string, [number, number]> = {
  sudan: [30.2, 15.6], chad: [18.7, 15.4], "south sudan": [30.3, 7.3],
  "dr congo": [23.7, -2.9], "democratic republic of the congo": [23.7, -2.9], haiti: [-72.7, 18.9],
  "united states": [-98.5, 39.8], russia: [99, 61.5], china: [104.2, 35.9],
  france: [2.2, 46.2], "united kingdom": [-1.5, 52.4], uk: [-1.5, 52.4],
  germany: [10.4, 51.2], italy: [12.6, 42.5], spain: [-3.7, 40.2],
  turkey: [35.2, 39.0], türkiye: [35.2, 39.0], iran: [53.7, 32.4],
  "united arab emirates": [54.3, 23.4], uae: [54.3, 23.4], qatar: [51.2, 25.3],
  "saudi arabia": [45.1, 23.9], egypt: [30.8, 26.8], libya: [17.2, 26.3],
  ukraine: [31.2, 48.4], belarus: [27.9, 53.7], serbia: [20.8, 44.2],
  israel: [34.9, 31.0], india: [78.9, 20.6], pakistan: [69.3, 30.4],
  "north korea": [127.5, 40.3], "south korea": [127.8, 36.5], japan: [138.2, 36.2],
  brazil: [-51.9, -14.2], "south africa": [22.9, -30.6], nigeria: [8.7, 9.1],
  ethiopia: [40.5, 9.1], kenya: [37.9, -0.02], uganda: [32.3, 1.4],
  poland: [19.1, 51.9], czechia: [15.5, 49.8], "czech republic": [15.5, 49.8],
  netherlands: [5.3, 52.1], sweden: [18.6, 60.1], norway: [8.5, 60.5],
  switzerland: [8.2, 46.8], canada: [-106.3, 56.1], australia: [133.8, -25.3],
};

export function centroidFor(key: string): [number, number] | null {
  return CENTROIDS[key.toUpperCase()] ?? NAME_CENTROIDS[key.toLowerCase()] ?? null;
}

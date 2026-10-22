// English and Spanish. Strings are keyed by their English text, with {name} placeholders, so the
// code reads as before; a string with no Spanish entry shows in English. The app subscribes once
// (useLang in App) and every component reads t() as it renders.
//
// Text the server writes (turn-by-turn steps, the conditions of a stretch, source names) stays in
// English for now.

import { useSyncExternalStore } from "react";

export type Lang = "en" | "es";
const KEY = "pathfinder.lang";

function initial(): Lang {
  const q = new URLSearchParams(window.location.search).get("lang");
  if (q === "en" || q === "es") return q;
  try {
    const s = localStorage.getItem(KEY);
    if (s === "en" || s === "es") return s;
  } catch { /* private browsing */ }
  return navigator.language?.toLowerCase().startsWith("es") ? "es" : "en";
}

let current: Lang = initial();
document.documentElement.lang = current;
const listeners = new Set<() => void>();

export function setLang(lang: Lang) {
  current = lang;
  try { localStorage.setItem(KEY, lang); } catch { /* private browsing */ }
  document.documentElement.lang = lang;
  listeners.forEach((f) => f());
}

export function useLang(): Lang {
  return useSyncExternalStore((cb) => { listeners.add(cb); return () => { listeners.delete(cb); }; }, () => current);
}

export function lang(): Lang { return current; }

/** The text in the current language, with {name} placeholders filled in. */
export function t(english: string, vars?: Record<string, string | number>): string {
  const s = current === "es" ? ES[english] ?? english : english;
  return vars ? s.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m)) : s;
}

/** A profile's label or description: the server's English, or its Spanish by profile id. */
export function tProfile(id: string, english: string, part: "label" | "description" = "label"): string {
  return current === "es" ? ES[`profile${part === "label" ? "" : "desc"}:${id}`] ?? english : english;
}

/** A word that changes with a count: plural("place", n) in either language. */
export function plural(n: number, one: string, many: string): string {
  return t(n === 1 ? one : many, { n });
}

const ES: Record<string, string> = {
  // header and search
  "curbs, slopes and sidewalks, as recorded": "bordillos, pendientes y aceras, según los registros",
  "Choose another place": "Elegir otro lugar",
  "Change place": "Cambiar de lugar",
  "Where from?": "¿Desde dónde?",
  "Where to?": "¿Adónde?",
  "My location": "Mi ubicación",
  "Swap start and destination": "Intercambiar origen y destino",
  "You are offline. The map and routes need a connection.": "No hay conexión. El mapa y las rutas la necesitan.",
  "Clear": "Borrar",
  "No match. Try a street address or a place name, or tap the map.": "Sin resultados. Pruebe una dirección o el nombre de un lugar, o toque el mapa.",
  "Type a place or address, or tap the map.": "Escriba un lugar o una dirección, o toque el mapa.",
  "The map could not load. Search and routes still work.": "No se pudo cargar el mapa. La búsqueda y las rutas siguen funcionando.",
  "Try again": "Intentar de nuevo",
  "Language": "Idioma",

  // tabs and panes
  "What matters": "Lo que importa",
  "Routes": "Rutas",
  "Barriers": "Barreras",
  "How I get around": "Cómo me desplazo",
  "Tap the one that fits you. You can fine-tune it below.": "Toque la opción que mejor le describa. Puede ajustarla abajo.",
  "Drag the point toward what matters most on this walk.": "Arrastre el punto hacia lo que más le importa en este trayecto.",
  "Each colour is a route. At this mix:": "Cada color es una ruta. Con esta combinación:",
  "the fastest route": "la ruta más rápida",
  "{m}, {extra} longer": "{m}, {extra} más",
  "Up to {n} min longer": "Hasta {n} min más",
  "Must have": "Imprescindible",
  "never traded away": "nunca se cede",
  "Step-free": "Sin escalones",
  "Any slope": "Cualquier pendiente",
  "Evidence I accept": "Datos que acepto",
  "Recorded only": "Solo registrados",
  "Recorded or likely": "Registrados o probables",
  "Anything not ruled out": "Todo lo no descartado",
  "Crossings & curbs": "Cruces y bordillos",
  "Slope": "Pendiente",
  "Sidewalk": "Acera",
  "crossings & curbs": "cruces y bordillos",
  "slope": "pendiente",
  "sidewalk": "acera",
  "walking": "caminando",
  "Priorities: drag to set the mix of crossings and curbs, slope, and sidewalk":
    "Prioridades: arrastre para combinar cruces y bordillos, pendiente y acera",

  // profiles (labels come from the server; translated here by id)
  "profile:manual_wheelchair": "Silla de ruedas manual",
  "profile:power_wheelchair": "Silla de ruedas eléctrica o scooter",
  "profile:walker_cane": "Andador o bastón",
  "profile:stroller": "Cochecito o carrito",
  "profile:custom": "Personalizado",
  "profiledesc:manual_wheelchair": "Sin escalones y sin pendientes sostenidas de más del 8,33 % (el límite de rampa de la ADA). La pendiente pesa más: cada subida se empuja a mano.",
  "profiledesc:power_wheelchair": "Sin escalones y sin pendientes sostenidas de más del 12 %. Los bordillos y las aceras rotas o inexistentes importan más que las cuestas.",
  "profiledesc:walker_cane": "Se permiten escalones, pero cuestan mucho. Los cruces largos o con tráfico, las superficies irregulares y caminar por la calzada pesan casi tanto como la pendiente.",
  "profiledesc:stroller": "Sin escalones. Lo que más importa es una buena acera; las cuestas, lo que menos.",
  "profiledesc:custom": "Defina sus propios requisitos y prioridades.",

  // routes
  "Ready when you are.": "Listo cuando usted quiera.",
  "Choose where from and where to, by searching above or tapping the map.": "Elija el origen y el destino buscando arriba o tocando el mapa.",
  "Try an example": "Pruebe un ejemplo",
  "Finding routes": "Buscando rutas",
  "Finding routes…": "Buscando rutas…",
  "Find routes": "Buscar rutas",
  "Start walking": "Empezar a caminar",
  "Start walking (demo)": "Empezar a caminar (demo)",
  "Fastest · best fit": "La más rápida · la mejor",
  "Best fit": "La mejor",
  "Fastest": "La más rápida",
  "Alternative": "Alternativa",
  "differs in {n} place": "cambia en {n} punto",
  "differs in {n} places": "cambia en {n} puntos",
  "+{extra} walking": "+{extra} caminando",
  ", feels {m} easier": ", se siente {m} más fácil",
  ", feels {m} harder at this mix": ", se siente {m} más difícil con esta combinación",
  "arrive {time}": "llegada {time}",
  "{walk} of walking plus {felt} of felt effort": "{walk} caminando más {felt} de esfuerzo percibido",
  "{n} more route wins elsewhere in the triangle. Drag the point under “What matters” to reach them.":
    "Hay {n} ruta más que gana en otra parte del triángulo. Arrastre el punto en «Lo que importa» para verla.",
  "{n} more routes win elsewhere in the triangle. Drag the point under “What matters” to reach them.":
    "Hay {n} rutas más que ganan en otras partes del triángulo. Arrastre el punto en «Lo que importa» para verlas.",
  "Numbered points on the map are where this route leaves the fastest one. Tap one to see why.":
    "Los puntos numerados del mapa son donde esta ruta se aparta de la más rápida. Toque uno para ver por qué.",
  "No route meets everything you asked for.": "Ninguna ruta cumple todo lo que pidió.",
  "Smallest compromise": "El menor compromiso",
  "{what}: {m}, {len}, with {n} stretch outside what you asked for.": "{what}: {m}, {len}, con {n} tramo fuera de lo que pidió.",
  "{what}: {m}, {len}, with {n} stretches outside what you asked for.": "{what}: {m}, {len}, con {n} tramos fuera de lo que pidió.",
  "Where you would be accepting it": "Dónde lo estaría aceptando",
  "allow slopes up to 10 %": "Permitir pendientes de hasta el 10 %",
  "accept places with no evidence": "Aceptar lugares sin datos",
  "allow steps and unverified curbs": "Permitir escalones y bordillos sin verificar",
  "Decision point": "Punto de decisión",
  "close": "cerrar",
  "{extra} longer here, and it feels {felt} easier.": "{extra} más aquí, y se siente {felt} más fácil.",
  "Your route · {len} m": "Su ruta · {len} m",
  "Fastest · {len} m": "La más rápida · {len} m",
  "Tell us how this is working": "Cuéntenos cómo le funciona",
  "Nothing notable is recorded on this stretch.": "No hay nada destacable registrado en este tramo.",

  // walking
  "You have arrived": "Ha llegado",
  "Set off heading {dir}.": "Salga en dirección {dir}.",
  "about {m} to go": "faltan unos {m}",
  "Route updated from where you are.": "Ruta actualizada desde donde está.",
  "You are {d} from the route. Finding a new one…": "Está a {d} de la ruta. Buscando otra…",
  "Show my position": "Mostrar mi posición",
  "Follow my position again": "Volver a seguir mi posición",
  "Re-center": "Centrar",

  // barriers and reports
  "What the city's and OpenStreetMap's records show in this view: barriers in colour, and in grey the places nobody has recorded. Tap one to see its source and date.":
    "Lo que muestran los registros en esta vista: las barreras en color y, en gris, los lugares que nadie ha registrado. Toque uno para ver su fuente y fecha.",
  "Barrier": "Barrera",
  "Sidewalk (estimated line)": "Acera (línea estimada)",
  "Not recorded": "Sin registrar",
  "Nothing here certifies a place as accessible.": "Nada de esto certifica que un lugar sea accesible.",
  "Report a barrier": "Informar de una barrera",
  "Tap the map where the barrier is.": "Toque el mapa donde está la barrera.",
  "What is there?": "¿Qué hay?",
  "Broken curb ramp": "Rampa rota",
  "No curb ramp": "Sin rampa",
  "Sidewalk blocked": "Acera bloqueada",
  "No sidewalk": "Sin acera",
  "Too steep": "Demasiado empinado",
  "Other": "Otro",
  "Anything else? (optional)": "¿Algo más? (opcional)",
  "Send report": "Enviar informe",
  "Cancel": "Cancelar",
  "Report another": "Informar de otra",
  "Thank you. Your report is saved for the team to check in person.": "Gracias. Su informe queda guardado para que el equipo lo revise en persona.",
  "Nothing changes on the map until someone has checked it on site. Only the place, what you chose and today's date are kept.":
    "Nada cambia en el mapa hasta que alguien lo compruebe en el lugar. Solo se guardan el lugar, lo que eligió y la fecha de hoy.",
  "That did not go through. Try again in a moment.": "No se pudo enviar. Inténtelo de nuevo en un momento.",
  "Report pin": "Marcador del informe",
  "Or use the centre of the map": "O usar el centro del mapa",
  "{n} route found.": "Se encontró {n} ruta.",
  "{n} routes found.": "Se encontraron {n} rutas.",
  "Selected: {name}, {m}.": "Seleccionada: {name}, {m}.",
};

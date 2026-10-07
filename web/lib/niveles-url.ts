// Lectura del nivel desde la URL (?nivel=). Solo para componentes de cliente.
import { parseAsStringLiteral } from "nuqs";
import { NIVEL_INICIAL, NIVELES } from "@/lib/niveles";

export const parseNivel = parseAsStringLiteral(NIVELES).withDefault(NIVEL_INICIAL);

const PRECISION = 4;


export function roundQuantity(value) {
  return Math.round(value * 10 ** PRECISION) / 10 ** PRECISION;
}

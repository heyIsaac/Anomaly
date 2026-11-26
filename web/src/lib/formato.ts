const brl2 = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 })
const brlExato = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 4 })
const num = new Intl.NumberFormat('pt-BR')

/** Limite e estatisticas: duas casas. O valor exato fica no banco. */
export const reais = (v: string | number) => brl2.format(Number(v))
/** Preco observado: mostra as casas que a fonte registrou (ate 4). */
export const precoFonte = (v: string | number) => brlExato.format(Number(v))
export const inteiro = (v: number) => num.format(v)

export function data(iso: string) {
  const [a, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${a}`
}

export function diferenca(preco: string, limite: string | null) {
  if (limite == null) return null
  return Number(preco) - Number(limite)
}

export const SITUACAO = {
  acima_da_referencia: 'Acima da referência',
  sem_alerta: 'Sem alerta',
  referencia_insuficiente: 'Referência insuficiente',
} as const

export function linkPncp(controle: string) {
  // 00394502000144-1-011884/2026 -> https://pncp.gov.br/app/editais/00394502000144/2026/11884
  const m = /^(\d{14})-\d+-(\d+)\/(\d{4})$/.exec(controle)
  return m ? `https://pncp.gov.br/app/editais/${m[1]}/${m[3]}/${Number(m[2])}` : null
}

export function linkCompras(idCompra: string, catmat: number) {
  return `https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial?tipo=codigoItemCatalogo&codigo=${catmat}&idCompra=${idCompra}`
}

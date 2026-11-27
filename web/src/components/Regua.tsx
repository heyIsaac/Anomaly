import { reais } from '@/lib/formato'

type Props = {
  precos: number[]
  observado: number
  q1: number | null
  mediana: number | null
  q3: number | null
  limite: number | null
  acima: boolean
  unidade: string
}

const L = 720, H = 196, ESQ = 24, DIR = 24, EIXO = 150, R = 5

function passo(span: number) {
  for (const p of [0.05, 0.1, 0.25, 0.5, 1, 2]) if (span / p <= 8) return p
  return 5
}

/** Reta de precos: comparaveis como pontos empilhados, faixa Q1-Q3, limite e o preco desta compra. */
export function Regua({ precos, observado, q1, mediana, q3, limite, acima, unidade }: Props) {
  const valores = [...precos, observado, ...(limite != null ? [limite] : [])]
  const p = passo(Math.max(...valores) - Math.min(...valores) || 1)
  const min = Math.floor((Math.min(...valores) - p / 2) / p) * p
  let max = Math.ceil((Math.max(...valores) + p / 2) / p) * p
  let x = (v: number) => ESQ + ((v - min) / (max - min)) * (L - ESQ - DIR)
  // Rotulos em lados opostos: o da compra vai para o lado de fora do limite.
  const direita = limite == null || observado >= limite
  const ROTULO = 170
  if (direita) while (x(observado) + ROTULO > L) { max += p; x = (v: number) => ESQ + ((v - min) / (max - min)) * (L - ESQ - DIR) }
  const ticks: number[] = []
  for (let t = min; t <= max + 1e-9; t += p) ticks.push(Math.round(t * 100) / 100)

  // Empilha pontos que caem no mesmo lugar, para mostrar precos repetidos. Com muitas compras os pontos
  // encolhem e a pilha se comprime para nao passar da faixa reservada (abaixo dos rotulos do topo).
  const r = precos.length > 40 ? 3 : R
  const pilhas = new Map<number, number>()
  const niveis = [...precos].sort((a, b) => a - b).map((v) => {
    const k = Math.round(x(v) / (r * 2))
    const nivel = pilhas.get(k) ?? 0
    pilhas.set(k, nivel + 1)
    return { cx: x(v), nivel }
  })
  const maiorPilha = Math.max(1, ...pilhas.values())
  const ALTURA = EIXO - 12 - 52 // espaco livre entre o eixo e os rotulos
  const passoY = Math.min(r * 2 + 2, ALTURA / maiorPilha)
  const pontos = niveis.map(({ cx, nivel }) => ({ cx, cy: EIXO - 12 - nivel * passoY }))

  const resumo =
    limite != null
      ? `${precos.length} preços de referência entre ${reais(Math.min(...precos))} e ${reais(Math.max(...precos))}. ` +
        `Limite em ${reais(limite)}. O preço desta compra, ${reais(observado)}, está ${acima ? 'acima' : 'dentro'} do limite.`
      : `${precos.length} preços de referência, abaixo do mínimo para calcular um limite.`

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${L} ${H}`} role="img" aria-label={resumo} className="h-auto w-full overflow-visible">
        {q1 != null && q3 != null && (
          <rect x={x(q1)} y={EIXO - 12 - ALTURA} width={Math.max(x(q3) - x(q1), 1)} height={ALTURA + 12} className="fill-faixa/35" />
        )}
        {mediana != null && (
          <line x1={x(mediana)} x2={x(mediana)} y1={EIXO - 12 - ALTURA} y2={EIXO} className="stroke-faixa" strokeWidth={2} />
        )}
        <line x1={ESQ} x2={L - DIR} y1={EIXO} y2={EIXO} className="stroke-apoio" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={EIXO} y2={EIXO + 6} className="stroke-apoio" />
            <text x={x(t)} y={EIXO + 22} textAnchor="middle" className="fill-apoio text-[13px]">
              {t.toFixed(2).replace('.', ',')}
            </text>
          </g>
        ))}
        {pontos.map((pt, i) => (
          <circle key={i} cx={pt.cx} cy={pt.cy} r={r} className="fill-tinta/75" />
        ))}
        {limite != null && (
          <g>
            <line x1={x(limite)} x2={x(limite)} y1={18} y2={EIXO} className="stroke-tinta" strokeWidth={1.5} strokeDasharray="4 4" />
            <text
              x={direita ? x(limite) - 6 : x(limite) + 6}
              y={direita ? 14 : 36}
              textAnchor={direita ? 'end' : 'start'}
              className="fill-tinta text-[13px] font-semibold"
            >
              Limite {reais(limite)}
            </text>
          </g>
        )}
        <g className="revelar-marca">
          <line x1={x(observado)} x2={x(observado)} y1={22} y2={EIXO} className="stroke-bomba" strokeWidth={3} />
          <path
            d={`M ${x(observado)} ${EIXO - 9} l 9 9 l -9 9 l -9 -9 z`}
            className={acima ? 'fill-bomba stroke-tinta' : 'fill-folha stroke-tinta'}
            strokeWidth={1.5}
          />
          <text
            x={direita ? x(observado) + 8 : x(observado) - 8}
            y={direita ? 36 : 14}
            textAnchor={direita ? 'start' : 'end'}
            className="fill-tinta text-[14px] font-bold"
          >
            Esta compra {reais(observado)}
          </text>
        </g>
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-apoio">
        <span><svg width="10" height="10" className="mr-1.5 inline fill-tinta/75 align-middle" aria-hidden><circle cx="5" cy="5" r="5" /></svg>Compras de referência</span>
        {q1 != null && <span><span className="mr-1.5 inline-block h-2.5 w-4 bg-faixa/35 align-middle" aria-hidden />Metade central dos preços (Q1 a Q3), com a mediana</span>}
        <span>Preços em R$ por {unidade}</span>
      </figcaption>
    </figure>
  )
}

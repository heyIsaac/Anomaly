import { Suspense } from 'react'
import Link from 'next/link'
import { contagens, loteAtual, municipios, ocorrencias, type Situacao } from '@/lib/dados'
import { SeloSituacao } from '@/components/Situacao'
import { data, diferenca, inteiro, precoFonte, reais, SITUACAO } from '@/lib/formato'

type Busca = Promise<{ [k: string]: string | string[] | undefined }>

const FILTROS: { valor: Situacao | 'todas'; rotulo: string }[] = [
  { valor: 'acima_da_referencia', rotulo: SITUACAO.acima_da_referencia },
  { valor: 'sem_alerta', rotulo: SITUACAO.sem_alerta },
  { valor: 'referencia_insuficiente', rotulo: SITUACAO.referencia_insuficiente },
  { valor: 'todas', rotulo: 'Todas' },
]

export default function Page({ searchParams }: { searchParams: Busca }) {
  return (
    <>
      <section className="max-w-3xl pt-12 pb-8">
        <h1 className="text-3xl font-bold leading-tight tracking-tight sm:text-[2.5rem]">
          Preços de gasolina comum pagos por órgãos públicos no Rio de Janeiro
        </h1>
        <p className="mt-4 max-w-[62ch] text-lg text-apoio">
          Cada compra é comparada com as compras de gasolina comum do mesmo estado nos 365 dias anteriores.
          Um preço acima da referência não prova irregularidade: indica onde vale olhar primeiro.
        </p>
      </section>
      <Suspense fallback={<p className="py-10 text-apoio">Carregando as compras…</p>}>
        <Lista searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function Lista({ searchParams }: { searchParams: Busca }) {
  const busca = await searchParams
  const lote = await loteAtual()
  if (!lote) {
    return (
      <p className="py-10 text-apoio">
        Nenhuma carga analisada ainda. Rode o importador com <code>uv run anomaly-import</code> e recarregue a página.
      </p>
    )
  }
  const pedido = typeof busca.situacao === 'string' ? busca.situacao : 'acima_da_referencia'
  const situacao = FILTROS.some((f) => f.valor === pedido) ? (pedido as Situacao | 'todas') : 'acima_da_referencia'
  const municipio = typeof busca.municipio === 'string' && busca.municipio ? busca.municipio : null
  const [linhas, totais, listaMunicipios] = await Promise.all([
    ocorrencias(lote.id, situacao === 'todas' ? null : situacao, municipio),
    contagens(lote.id),
    municipios(lote.id),
  ])
  const total = totais.acima_da_referencia + totais.sem_alerta + totais.referencia_insuficiente
  const fora = (lote.classes.gestao ?? 0) + (lote.classes.nao_unitario ?? 0) + (lote.classes.indeterminado ?? 0)
  const qs = (s: string) => `/?situacao=${s}${municipio ? `&municipio=${encodeURIComponent(municipio)}` : ''}`

  return (
    <>
      <p className="max-w-[72ch] border-l-2 border-faixa pl-4 text-[0.9375rem] text-apoio">
        Carga de {data(lote.extraido_em)} do Compras.gov.br (CATMAT {lote.catmat}), com {inteiro(lote.total_unico)} itens
        de compra no país. {inteiro(lote.classes.preco_litro ?? 0)} trazem preço por litro e entram nas referências.
        Ficaram fora {inteiro(fora)}: {inteiro(lote.classes.gestao ?? 0)} contratos de gestão de abastecimento,{' '}
        {inteiro(lote.classes.nao_unitario ?? 0)} valores que não são preço por litro e{' '}
        {inteiro(lote.classes.indeterminado ?? 0)} sem significado confirmado. Aqui aparecem as {inteiro(total)} compras
        do RJ.
      </p>

      <div className="mt-10 flex flex-col gap-4 border-b border-fio pb-4 md:flex-row md:items-end md:justify-between">
        <nav aria-label="Filtrar por situação" className="flex flex-wrap gap-x-6 gap-y-2">
          {FILTROS.map((f) => {
            const ativo = f.valor === situacao
            const n = f.valor === 'todas' ? total : totais[f.valor]
            return (
              <Link
                key={f.valor}
                href={qs(f.valor)}
                aria-current={ativo ? 'page' : undefined}
                className={`pb-1 no-underline ${ativo ? 'border-b-2 border-tinta font-semibold' : 'text-apoio hover:text-tinta'}`}
              >
                {f.rotulo} <span className="text-apoio">{inteiro(n)}</span>
              </Link>
            )
          })}
        </nav>
        <form className="flex items-end gap-2" action="/">
          <input type="hidden" name="situacao" value={situacao} />
          <label className="flex flex-col text-sm text-apoio">
            Município
            <select
              name="municipio"
              defaultValue={municipio ?? ''}
              className="mt-1 rounded border border-fio bg-folha px-2 py-1.5 text-base text-tinta"
            >
              <option value="">Todos</option>
              {listaMunicipios.map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
          <button className="rounded border border-tinta px-3 py-1.5 font-medium hover:bg-tinta hover:text-papel">
            Filtrar
          </button>
        </form>
      </div>

      {linhas.length === 0 ? (
        <p className="py-10 text-apoio">
          Nenhuma compra nesta situação{municipio ? ` em ${municipio}` : ''}.{' '}
          <Link href="/?situacao=todas">Ver todas as compras do RJ</Link>.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] border-collapse text-left">
            <caption className="sr-only">Compras de gasolina comum do RJ e a situação de cada preço</caption>
            <thead className="text-sm text-apoio">
              <tr className="border-b border-fio">
                <th scope="col" className="py-3 pr-4 font-medium">Data</th>
                <th scope="col" className="py-3 pr-4 font-medium">Comprador</th>
                <th scope="col" className="py-3 pr-4 text-right font-medium">Preço por litro</th>
                <th scope="col" className="py-3 pr-4 text-right font-medium">Em relação ao limite</th>
                <th scope="col" className="py-3 font-medium">Situação</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map((o) => {
                const d = diferenca(o.preco_observado, o.limite)
                return (
                  <tr key={o.id_compra_item} className="group border-b border-fio/70 hover:bg-folha">
                    <td className="py-3 pr-4 align-top whitespace-nowrap text-apoio">{data(o.data_compra)}</td>
                    <td className="py-3 pr-4 align-top">
                      <Link href={`/compras/${o.id_compra_item}`} className="font-medium decoration-fio group-hover:decoration-tinta">
                        {o.municipio}
                      </Link>
                      <div className="text-sm text-apoio">{o.nome_orgao}</div>
                    </td>
                    <td className="py-3 pr-4 text-right align-top text-lg font-semibold">{precoFonte(o.preco_observado)}</td>
                    <td className={`py-3 pr-4 text-right align-top ${d != null && d > 0 ? 'font-medium text-alerta' : 'text-apoio'}`}>
                      {d == null ? 'sem limite' : `${d > 0 ? '+' : '−'}${reais(Math.abs(d))}`}
                    </td>
                    <td className="py-3 align-top"><SeloSituacao situacao={o.situacao} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

import { Suspense } from 'react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { comparaveis, detalhe, loteDe, lotesAtuais, type Comparavel } from '@/lib/dados'
import { Regua } from '@/components/Regua'
import { Origem } from '@/components/Origem'
import { SeloSituacao } from '@/components/Situacao'
import { data, inteiro, precoFonte, quantidadeComprada, reais, unidadeCurta } from '@/lib/formato'

type Params = Promise<{ id: string }>

export default function Page({ params }: { params: Params }) {
  return (
    <>
      <p className="pt-8">
        <Link href="/" className="text-sm text-apoio hover:text-tinta">Voltar para a lista de compras</Link>
      </p>
      <Suspense fallback={<p className="py-10 text-apoio">Carregando a compra…</p>}>
        <Conteudo params={params} />
      </Suspense>
    </>
  )
}

function veredito(sit: string, preco: number, limite: number | null, n: number, minimo: number, motivo: string | null) {
  if (sit === 'acima_da_referencia' && limite != null)
    return `${reais(preco - limite)} acima do limite calculado com ${inteiro(n)} compras do mesmo estado.`
  if (sit === 'sem_alerta' && limite != null)
    return `Dentro do limite: ${reais(limite - preco)} abaixo do valor que geraria alerta.`
  return motivo?.startsWith('IQR')
    ? 'As compras de referência têm todas o mesmo preço, então não há dispersão para calcular um limite.'
    : n === 0
      ? `Nenhuma compra do mesmo estado no período; a regra pede pelo menos ${minimo}.`
      : `Só ${inteiro(n)} ${n === 1 ? 'compra' : 'compras'} do mesmo estado no período; a regra pede pelo menos ${minimo}.`
}

async function Conteudo({ params }: { params: Params }) {
  const { id } = await params
  const lotes = await lotesAtuais()
  const d = await detalhe(lotes.map((l) => l.id), id)
  if (!d) notFound()
  const lote = lotes.find((l) => l.id === d.lote_id) ?? (await loteDe(d.lote_id))
  if (!lote) notFound()
  const unidade = lote.unidade_comparacao
  const nome = lote.nome_categoria.toLowerCase().replace('a4', 'A4')
  const capacidade = d.capacidade && d.capacidade > 0 ? d.capacidade : null
  const refs = await comparaveis(d.avaliacao_id)
  const preco = Number(d.preco_observado)
  const limite = d.limite != null ? Number(d.limite) : null
  const acima = d.situacao === 'acima_da_referencia'
  const [, uf] = d.grupo.split(':')

  return (
    <article>
      <header className="max-w-4xl pt-6">
        <SeloSituacao situacao={d.situacao} />
        <h1 className="mt-4 text-2xl font-semibold leading-snug sm:text-3xl">
          {d.nome_orgao}, {d.municipio}
        </h1>
        <p className="mt-1 text-apoio">
          {lote.nome_categoria}, compra de {data(d.data_compra)}:{' '}
          {quantidadeComprada(lote.categoria, Number(d.quantidade), capacidade)}
        </p>
        <p className="mt-6 text-5xl font-bold tracking-tight sm:text-6xl">
          {precoFonte(d.preco_observado)}
          <span className="ml-2 text-xl font-medium text-apoio">por {unidade}</span>
        </p>
        {capacidade != null && Number(d.preco_unitario) !== Number(d.preco_observado) && (
          <p className="mt-1 text-apoio">
            Preço registrado: {precoFonte(d.preco_unitario)} por pacote de {inteiro(capacidade)} folhas
          </p>
        )}
        <p className={`mt-3 max-w-[60ch] text-lg ${acima ? 'font-medium text-alerta' : ''}`}>
          {veredito(d.situacao, preco, limite, d.n, d.minimo, d.motivo)}
        </p>
      </header>

      <section aria-labelledby="t-regua" className="mt-12">
        <h2 id="t-regua" className="text-lg font-semibold">Como este preço se compara</h2>
        <p className="mt-1 max-w-[70ch] text-apoio">
          Compras de {nome}, por {unidade}, feitas por órgãos do {uf} entre {data(d.janela_inicio)} e{' '}
          {data(d.janela_fim)}, os 365 dias anteriores a esta compra.
        </p>
        <div className="mt-6 overflow-x-auto rounded-md bg-folha px-3 py-5 sm:px-6">
          {refs.length > 0 ? (
            <div className="min-w-[38rem]">
              <Regua
                precos={refs.map((r) => Number(r.preco_unitario))}
                observado={preco}
                q1={d.q1 != null ? Number(d.q1) : null}
                mediana={d.mediana != null ? Number(d.mediana) : null}
                q3={d.q3 != null ? Number(d.q3) : null}
                limite={limite}
                acima={acima}
                unidade={unidade}
              />
            </div>
          ) : (
            <p className="text-apoio">Nenhuma compra do {uf} nesse período para comparar.</p>
          )}
        </div>

        <dl className="mt-8 grid max-w-4xl grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4">
          <Numero rotulo="Compras de referência" valor={inteiro(d.n)} nota={`mínimo ${d.minimo}`} />
          <Numero rotulo="Mediana" valor={d.mediana ? reais(d.mediana) : 'não calculada'} />
          <Numero
            rotulo="Q1 e Q3"
            valor={d.q1 && d.q3 ? `${reais(d.q1)} e ${reais(d.q3)}` : 'não calculados'}
            nota={d.iqr ? `distância de ${reais(d.iqr)}` : undefined}
          />
          <Numero rotulo="Limite" valor={limite != null ? reais(limite) : 'sem limite'} nota="Q3 + 1,5 × (Q3 − Q1)" />
        </dl>
        <p className="mt-6 max-w-[70ch] text-sm text-apoio">
          Um preço recebe alerta quando é maior que o limite. Igualar o limite não gera alerta. Regra{' '}
          {d.versao_regra}, carga {lote.id} de {data(lote.extraido_em)}.
        </p>
      </section>

      <div className="mt-14 grid gap-12 lg:grid-cols-[3fr_2fr]">
        <section aria-labelledby="t-objeto">
          <h2 id="t-objeto" className="text-lg font-semibold">O que foi contratado</h2>
          <p className="mt-1 text-sm text-apoio">Texto do registro de origem</p>
          <blockquote className="mt-4 max-w-[68ch] border-l-2 border-tinta pl-5 font-fonte text-[1.125rem] leading-[1.7]">
            {d.objeto}
          </blockquote>
          {d.pistas_revisao.length > 0 && (
            <p className="mt-4 text-sm text-apoio">Pontos a conferir no registro: {d.pistas_revisao.join('; ')}.</p>
          )}
        </section>
        <section aria-labelledby="t-origem">
          <h2 id="t-origem" className="text-lg font-semibold">Registro de origem</h2>
          <div className="mt-4"><Origem d={d} catmat={d.catmat} /></div>
        </section>
      </div>

      {refs.length > 0 && (
        <section aria-labelledby="t-refs" className="mt-14">
          <h2 id="t-refs" className="text-lg font-semibold">As {inteiro(refs.length)} compras usadas na referência</h2>
          {refs.length > 12 && (
            <p className="mt-1 text-sm text-apoio">As 10 de maior preço por {unidade}. As demais ficam logo abaixo.</p>
          )}
          <TabelaRefs refs={refs.length > 12 ? refs.slice(0, 10) : refs} unidade={unidade} />
          {refs.length > 12 && (
            <details className="mt-4">
              <summary className="cursor-pointer font-medium">Mostrar as outras {inteiro(refs.length - 10)} compras</summary>
              <TabelaRefs refs={refs.slice(10)} unidade={unidade} />
            </details>
          )}
        </section>
      )}
    </article>
  )
}

function Numero({ rotulo, valor, nota }: { rotulo: string; valor: string; nota?: string }) {
  return (
    <div>
      <dt className="text-sm text-apoio">{rotulo}</dt>
      <dd className="mt-1 text-xl font-semibold">{valor}</dd>
      {nota && <dd className="text-sm text-apoio">{nota}</dd>}
    </div>
  )
}

function TabelaRefs({ refs, unidade }: { refs: Comparavel[]; unidade: string }) {
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[36rem] border-collapse text-left text-[0.9375rem]">
        <thead className="text-sm text-apoio">
          <tr className="border-b border-fio">
            <th scope="col" className="py-2 pr-4 font-medium">Data</th>
            <th scope="col" className="py-2 pr-4 font-medium">Comprador</th>
            <th scope="col" className="py-2 text-right font-medium">Preço por {unidadeCurta(unidade)}</th>
          </tr>
        </thead>
        <tbody>
          {refs.map((r) => (
            <tr key={r.id_compra_item} className="border-b border-fio/70">
              <td className="py-2 pr-4 whitespace-nowrap text-apoio">{data(r.data_compra)}</td>
              <td className="py-2 pr-4">{r.nome_orgao}, {r.municipio}</td>
              <td className="py-2 text-right font-medium">{precoFonte(r.preco_unitario)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

import type { Detalhe } from '@/lib/dados'
import { linkCompras, linkPncp } from '@/lib/formato'

const AVISO: Record<Exclude<Detalhe['origem_status'], 'confirmada'>, string> = {
  ausente_no_pncp:
    'Este item não foi localizado no PNCP. Contratações anteriores à Lei 14.133 costumam estar só no Compras.gov.br.',
  nao_consultada: 'A conferência no PNCP ainda não foi feita para esta carga.',
  erro: 'A consulta ao PNCP falhou na última carga. Isso não indica que o registro não existe; a conferência será refeita na próxima carga.',
}

export function Origem({ d, catmat }: { d: Detalhe; catmat: number }) {
  const pncp = d.origem_status === 'confirmada' && d.numero_controle_pncp ? linkPncp(d.numero_controle_pncp) : null
  return (
    <div className="space-y-4">
      {pncp ? (
        <p>
          <a href={pncp} className="text-lg font-semibold" target="_blank" rel="noreferrer">
            Abrir a contratação no PNCP
          </a>
          <span className="block break-all text-sm text-apoio">Número de controle {d.numero_controle_pncp}</span>
        </p>
      ) : (
        <p className="max-w-[62ch]">{AVISO[d.origem_status as keyof typeof AVISO] ?? AVISO.nao_consultada}</p>
      )}
      <dl className="grid grid-cols-1 gap-x-6 sm:grid-cols-[max-content_1fr] sm:gap-y-1 text-[0.9375rem] [&_dd]:break-all [&_dd]:mb-2 sm:[&_dd]:mb-0">
        <dt className="text-apoio">Compra no Compras.gov.br</dt>
        <dd>{d.id_compra}</dd>
        <dt className="text-apoio">Número do item</dt>
        <dd>{d.numero_item ?? 'não informado'}</dd>
        <dt className="text-apoio">Identificador do item</dt>
        <dd className="break-all">{d.id_compra_item}</dd>
        <dt className="text-apoio">UASG</dt>
        <dd>{d.codigo_uasg}</dd>
      </dl>
      <p>
        <a href={linkCompras(d.id_compra, catmat)} target="_blank" rel="noreferrer">
          Ver o registro original na API do Compras.gov.br
        </a>
      </p>
    </div>
  )
}

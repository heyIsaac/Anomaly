import type { Situacao } from '@/lib/dados'
import { SITUACAO } from '@/lib/formato'

const estilo: Record<Situacao, string> = {
  acima_da_referencia: 'border border-bomba/70 bg-alerta-fundo text-alerta',
  sem_alerta: 'border border-fio text-apoio',
  referencia_insuficiente: 'border border-dashed border-apoio/60 text-apoio',
}

export function SeloSituacao({ situacao }: { situacao: Situacao }) {
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[0.8125rem] font-medium ${estilo[situacao]}`}>
      {SITUACAO[situacao]}
    </span>
  )
}

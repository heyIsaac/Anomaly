import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="max-w-xl py-16">
      <h1 className="text-2xl font-semibold">Compra não encontrada nesta carga</h1>
      <p className="mt-3 text-apoio">
        O endereço pode ser de uma carga anterior ou de um item que não entrou na análise do RJ.
      </p>
      <p className="mt-6"><Link href="/">Voltar para a lista de compras</Link></p>
    </div>
  )
}

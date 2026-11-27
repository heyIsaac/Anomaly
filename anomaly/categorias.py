"""Categorias de compra. Cada uma sabe classificar um registro e levar o preco para a unidade de comparacao.

classificar(x) devolve (classe, motivo, preco_normalizado). So a classe `valida` entra na referencia.
"""
import json, re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from . import classificar as gasolina_cls


@dataclass
class Categoria:
    slug: str
    nome: str
    unidade: str            # unidade de comparacao exibida: "litro", "resma de 500 folhas"
    valida: str             # classe que entra na referencia
    versao: str
    codigo_tipo: str = 'CATMAT'
    catalogo: dict = field(default_factory=dict)

    def classificar(self, x):
        raise NotImplementedError

    def pistas(self, x):
        return []


class Gasolina(Categoria):
    def __init__(self, **_):
        super().__init__('gasolina', 'Gasolina comum', 'litro', 'preco_litro', gasolina_cls.VERSAO)

    def classificar(self, x):
        classe, motivo = gasolina_cls.classificar(x)
        return classe, motivo, x['precoUnitario'] if classe == self.valida else None

    def pistas(self, x):
        return gasolina_cls.pistas(x)


PAPEL_FAIXA = (Decimal('10'), Decimal('80'))  # R$ por resma de 500 folhas plausivel
# Objeto ou descricao que nomeia outro papel: o codigo diz sulfite, mas a compra e de outra coisa.
OUTRO_PAPEL = re.compile(r'couch[eê]|verg[eê]|reciclad|fotogr[aá]fic|certifica|opaline|color ?plus|cart[aã]o|adesiv', re.I)

PAPEL_NOMEADO = re.compile(r'pap(?:el|[eé]is)\s+(?:' + OUTRO_PAPEL.pattern + r')', re.I)
A4_NO_OBJETO = re.compile(r'\bA4\b|sulfite|apergaminhad|of[ií]cio|papel para impress|expediente|escrit[oó]rio', re.I)


class PapelA4(Categoria):
    """Papel A4 branco 75 g/m2 (PDM 19746). Compara so embalagens de 500 folhas: pacotes menores
    custam mais por folha e costumam ser papel especial (bancada de 2026-11-26)."""

    def __init__(self, catalogo: Path | None = None, **_):
        cat = {}
        if catalogo:
            cat = {x['codigoItem']: x['descricaoItem'] for x in json.loads(Path(catalogo).read_text())['resultado']}
        super().__init__('papel-a4', 'Papel A4 branco 75 g/m²', 'resma de 500 folhas', 'preco_resma',
                         'papel-v1', 'PDM', cat)

    @staticmethod
    def a4_branco_75(desc):
        return bool(re.search(r'297 X 210', desc) and re.search(r'GRAMATURA: 75 G', desc) and re.search(r'COR: BRANC', desc))

    def classificar(self, x):
        desc = self.catalogo.get(x.get('codigoItemCatalogo'), '')
        if not self.a4_branco_75(desc):
            return 'outro_item', 'codigo de catalogo nao e A4 branco 75 g/m2', None
        m = OUTRO_PAPEL.search(f"{x.get('descricaoItem') or ''} {x.get('marca') or ''}")
        if m:
            return 'outro_item', f"descricao ou marca cita '{m.group(0)}': outro tipo de papel sob o codigo de sulfite", None
        objeto = x.get('objetoCompra') or ''
        m = PAPEL_NOMEADO.search(objeto)  # objeto costuma listar varios materiais: so 'papel <tipo>' conta
        if m and not A4_NO_OBJETO.search(objeto):
            return 'outro_item', f"objeto da compra e de '{m.group(0)}' e nao cita A4 ou sulfite", None
        p = x.get('precoUnitario')
        if p is None or p <= 0:
            return 'indeterminado', 'preco ausente ou nao positivo', None
        sig, cap, med = x.get('siglaUnidadeFornecimento'), x.get('capacidadeUnidadeFornecimento') or 0, x.get('siglaUnidadeMedida')
        if not (sig == 'EMB' and med == 'FL' and cap > 0):
            return 'indeterminado', f'embalagem sem numero de folhas ({sig}, {cap:g}, {med})', None
        if cap != 500:
            return 'outra_embalagem', f'embalagem de {cap:g} folhas; a referencia compara so resmas de 500', None
        if not PAPEL_FAIXA[0] <= p <= PAPEL_FAIXA[1]:
            return 'indeterminado', f'R$ {p} por resma fora da faixa de R$ 10 a R$ 80', None
        if not x.get('dataCompra'):
            return 'indeterminado', 'sem data da compra', None
        return 'preco_resma', 'resma de 500 folhas', p

    def pistas(self, x):
        out = []
        if (x.get('criterioJulgamento') or '').strip() == 'D':
            out.append('criterio de julgamento por desconto')
        return out


CATEGORIAS = {'gasolina': Gasolina, 'papel-a4': PapelA4}
